"""Email detection pipeline orchestrating all handlers."""

import asyncio
import re
import time
from typing import Any

from api_structure.core.logger import set_extract_log
from api_structure.core.timer import timed
from api_structure.src.clients.aiohttp_client import AiohttpClient
from api_structure.src.clients.google_translate import GoogleTranslateClient
from api_structure.src.clients.gpt import GptClient
from api_structure.src.handlers.email_split import generate_email_split
from api_structure.src.handlers.email_summary import generate_email_summary
from api_structure.src.handlers.email_translate import translate_to_english
from api_structure.src.handlers.vector_search import search_vector_kb
from api_structure.src.utils.product_line_mapping import find_productline


class EmailDetectPipeline:
    """Pipeline for email detection and analysis."""

    def __init__(
        self,
        gpt_client: GptClient,
        google_translate_client: GoogleTranslateClient,
        aiohttp_client: AiohttpClient,
    ):
        """Initialize pipeline with required clients.

        Args:
            gpt_client: Initialized GPT client.
            google_translate_client: Initialized Google Translate client.
            aiohttp_client: Initialized aiohttp client.
        """
        self.gpt_client = gpt_client
        self.google_translate_client = google_translate_client
        self.aiohttp_client = aiohttp_client

        self.summary = None
        self.lang = "error"
        self.product_line = "error"

    async def _call_api_process(
        self, sentence_org: str, product_line: str, website: str
    ) -> tuple[str, dict, dict, dict]:
        """Process sentence through translate and vector search.

        Args:
            sentence_org: Original sentence text.
            product_line: Product line identifier.
            website: Website code.

        Returns:
            Tuple of (translate_result, api_return, intent, kb).
        """
        translate_result = await translate_to_english(
            self.gpt_client, self.google_translate_client, sentence_org
        )

        api_return, api_intent, api_kb = await search_vector_kb(
            self.aiohttp_client, translate_result, product_line, website
        )

        return translate_result, api_return, api_intent, api_kb

    @timed(task_name="generate_check_info")
    async def _generate_check_info(
        self, input_product_content: str, product_line: str, site: str
    ) -> tuple[list[dict], str, str]:
        """Generate check info from email content.

        Args:
            input_product_content: Product problem description.
            product_line: Product line identifier.
            site: Website code.

        Returns:
            Tuple of (email_split_info, lang, summary).

        Raises:
            RuntimeError: If API call fails.
            Exception: If check info generation fails.
        """
        # Generate summary
        summary, lang = await generate_email_summary(
            self.gpt_client, input_product_content
        )
        self.summary = summary
        self.lang = lang

        # Generate split
        split_json = await generate_email_split(
            self.gpt_client, input_product_content, lang
        )

        # Process summary
        extra_summary = {
            "summary": asyncio.create_task(
                self._call_api_process(summary, product_line, site)
            )
        }

        # Process split sentences
        split_task = {
            key: asyncio.create_task(
                self._call_api_process(value, product_line, site)
            )
            for key, value in split_json.items()
            if re.match(r"extracted_sentence(\d+)", key)
        }
        split_task.update(extra_summary)

        # Wait for all tasks
        split_task_result = await asyncio.gather(*split_task.values())

        # Extract API logs
        api_log_list = [value[1] for value in split_task_result]

        # Check API success
        api_kb_log_check = [
            0 if value[1].get("success") else 1 for value in split_task_result
        ]
        if sum(api_kb_log_check) > 0:
            raise RuntimeError("API call error")

        # Build email split info
        translate_list = [value[0] for value in split_task_result]
        api_intent_list = [value[2] for value in split_task_result]
        api_kb_list = [value[3] for value in split_task_result]
        extract_type = [
            "split" if "extracted_sentence" in key else "summary"
            for key in split_task.keys()
        ]
        extract_type_num = [
            int(key[-1]) if "extracted_sentence" in key else None
            for key in split_task.keys()
        ]
        split_json_keys = list(split_task.keys())

        email_split_info = []
        for (
            split_key,
            translate,
            api_log,
            api_intent,
            api_kb,
            ext_type,
            ext_num,
        ) in zip(
            split_json_keys,
            translate_list,
            api_log_list,
            api_intent_list,
            api_kb_list,
            extract_type,
            extract_type_num,
        ):
            try:
                gpt_org = split_json.get(split_key, summary)
                # Validate intent result
                api_intent["intent_1"]
                api_intent["cosineSimilarity_1"]
                api_intent["key_1"]
            except Exception as e:
                raise Exception(f"Generate check info error: {e}")

            email_split_info_ = {
                "extract_type": ext_type,
                "extract_type_num": ext_num,
                "gpt_output_org": gpt_org,
                "gpt_output": translate,
                "intent": api_intent["intent_1"],
                "intent_similarity": api_intent["cosineSimilarity_1"],
                "intent_key": api_intent["key_1"],
                "top1_kb": api_kb["kb_no_1"],
                "top1_kb_similarity": api_kb["cosineSimilarity_1"],
                "key_1": api_kb["key_1"],
                "top2_kb": api_kb["kb_no_2"],
                "top2_kb_similarity": api_kb["cosineSimilarity_2"],
                "key_2": api_kb["key_2"],
                "top3_kb": api_kb["kb_no_3"],
                "top3_kb_similarity": api_kb["cosineSimilarity_3"],
                "key_3": api_kb["key_3"],
                "top4_kb": api_kb["kb_no_4"],
                "top4_kb_similarity": api_kb["cosineSimilarity_4"],
                "key_4": api_kb["key_4"],
                "api_log": api_log,
            }
            email_split_info.append(email_split_info_)

        return email_split_info, lang, summary

    def _generate_gpt_extract(
        self, email_split_info: list[dict]
    ) -> list[dict]:
        """Generate GPT extract from split info using business rules.

        Args:
            email_split_info: List of split info dictionaries.

        Returns:
            List of extracted sentences matching criteria.
        """
        # Case 1: Split with high similarity
        output_list_case1 = []
        for lst in email_split_info:
            if lst["extract_type"] == "summary":
                continue
            if lst["intent"] in ["Only Chat", "Greeting"]:
                continue

            if lst["intent"] != "Technical Support":
                if lst["intent_similarity"] >= 0.6:
                    tmp_dict = {
                        "extract_type": lst["extract_type"],
                        "extract_type_num": lst["extract_type_num"],
                        "gpt_output": lst["gpt_output_org"],
                        "intent": lst["intent"],
                        "top1_simi": lst["top1_kb_similarity"],
                        "top1_kb": None,
                        "top2_kb": None,
                        "top3_kb": None,
                        "top4_kb": None,
                    }
                    output_list_case1.append(tmp_dict)
            else:
                if lst["top1_kb_similarity"] >= 0.71:
                    tmp_dict = {
                        "extract_type": lst["extract_type"],
                        "extract_type_num": lst["extract_type_num"],
                        "gpt_output": lst["gpt_output_org"],
                        "intent": lst["intent"],
                        "top1_simi": lst["top1_kb_similarity"],
                        "top1_kb": lst["top1_kb"],
                        "top2_kb": lst["top2_kb"],
                        "top3_kb": lst["top3_kb"],
                        "top4_kb": lst["top4_kb"],
                    }
                    output_list_case1.append(tmp_dict)

        # Case 2: Best technical support split
        note_case2_max_similarity = 0
        tmp_dict = {}
        for lst in email_split_info:
            if lst["extract_type"] == "summary":
                continue
            if (
                lst["intent"] == "Technical Support"
                and lst["top1_kb_similarity"] >= 0.695
            ):
                if lst["top1_kb_similarity"] > note_case2_max_similarity:
                    note_case2_max_similarity = lst["top1_kb_similarity"]
                    tmp_dict = {
                        "extract_type": lst["extract_type"],
                        "extract_type_num": lst["extract_type_num"],
                        "gpt_output": lst["gpt_output_org"],
                        "intent": lst["intent"],
                        "top1_simi": lst["top1_kb_similarity"],
                        "top1_kb": lst["top1_kb"],
                        "top2_kb": lst["top2_kb"],
                        "top3_kb": lst["top3_kb"],
                        "top4_kb": lst["top4_kb"],
                    }
        output_list_case2 = [tmp_dict] if note_case2_max_similarity > 0 else []

        # Case 3: Summary-based extraction
        note_case3_target = [
            lst for lst in email_split_info if lst["extract_type"] == "summary"
        ][0]
        note_case3_target_intent = note_case3_target["intent"]

        tmp_dict = {}
        if (
            note_case3_target_intent == "Technical Support"
            and note_case3_target["top1_kb_similarity"] >= 0.695
        ):
            note_case3_target_top1_kb = note_case3_target["top1_kb"]
            note_case3_max_similarity = 0

            for lst in email_split_info:
                if lst["extract_type"] == "summary":
                    continue
                if (
                    note_case3_target_intent == lst["intent"]
                    and note_case3_target_top1_kb == lst["top1_kb"]
                    and note_case3_max_similarity < lst["top1_kb_similarity"]
                ):
                    note_case3_max_similarity = lst["top1_kb_similarity"]
                    tmp_dict = {
                        "extract_type": lst["extract_type"],
                        "extract_type_num": lst["extract_type_num"],
                        "gpt_output": lst["gpt_output_org"],
                        "intent": lst["intent"],
                        "top1_simi": lst["top1_kb_similarity"],
                        "top1_kb": lst["top1_kb"],
                        "top2_kb": lst["top2_kb"],
                        "top3_kb": lst["top3_kb"],
                        "top4_kb": lst["top4_kb"],
                    }

            if len(tmp_dict) == 0:
                tmp_dict = {
                    "extract_type": note_case3_target["extract_type"],
                    "extract_type_num": note_case3_target["extract_type_num"],
                    "gpt_output": note_case3_target["gpt_output_org"],
                    "intent": note_case3_target["intent"],
                    "top1_simi": note_case3_target["top1_kb_similarity"],
                    "top1_kb": note_case3_target["top1_kb"],
                    "top2_kb": note_case3_target["top2_kb"],
                    "top3_kb": note_case3_target["top3_kb"],
                    "top4_kb": note_case3_target["top4_kb"],
                }
        elif (
            note_case3_target_intent
            not in ["Technical Support", "Only Chat", "Greeting"]
            and note_case3_target["intent_similarity"] >= 0.6
        ):
            note_case3_max_similarity = 0

            for lst in email_split_info:
                if lst["extract_type"] == "summary":
                    continue
                if (
                    note_case3_target_intent == lst["intent"]
                    and note_case3_max_similarity < lst["intent_similarity"]
                ):
                    note_case3_max_similarity = lst["intent_similarity"]
                    tmp_dict = {
                        "extract_type": lst["extract_type"],
                        "extract_type_num": lst["extract_type_num"],
                        "gpt_output": lst["gpt_output_org"],
                        "intent": lst["intent"],
                        "top1_simi": lst["top1_kb_similarity"],
                        "top1_kb": None,
                        "top2_kb": None,
                        "top3_kb": None,
                        "top4_kb": None,
                    }

            if len(tmp_dict) == 0:
                tmp_dict = {
                    "extract_type": note_case3_target["extract_type"],
                    "extract_type_num": note_case3_target["extract_type_num"],
                    "gpt_output": note_case3_target["gpt_output_org"],
                    "intent": note_case3_target["intent"],
                    "top1_simi": note_case3_target["top1_kb_similarity"],
                    "top1_kb": None,
                    "top2_kb": None,
                    "top3_kb": None,
                    "top4_kb": None,
                }

        output_list_case3 = [tmp_dict] if len(tmp_dict) > 0 else []

        # Priority: case1 > case2 > case3
        if len(output_list_case1) > 0:
            return output_list_case1
        elif len(output_list_case2) > 0:
            return output_list_case2
        elif len(output_list_case3) > 0:
            return output_list_case3
        else:
            return []

    def _num_recode(
        self, email_split_sentence: list[dict], email_split_info: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """Renumber extracted sentences and map indices.

        Args:
            email_split_sentence: Extracted sentences to renumber.
            email_split_info: Full split info to update.

        Returns:
            Tuple of (renumbered_sentences, updated_split_info).
        """
        output_email_split_sentence = {}
        index_transform_dict = {}
        i_ = 1

        for item in email_split_sentence:
            raw_index = item["extract_type_num"]
            key = (
                item["top1_kb"]
                if item["intent"] == "Technical Support"
                else item["gpt_output"]
            )

            if key not in output_email_split_sentence:
                output_email_split_sentence[key] = item.copy()
                output_email_split_sentence[key]["extract_type_num"] = i_
                index_transform_dict[raw_index] = i_
                i_ += 1
            else:
                index_transform_dict[raw_index] = output_email_split_sentence[
                    key
                ]["extract_type_num"]
                output_email_split_sentence[key]["gpt_output"] += (
                    " " + item["gpt_output"]
                )
                if (
                    item["top1_simi"]
                    > output_email_split_sentence[key]["top1_simi"]
                ):
                    output_email_split_sentence[key]["top2_kb"] = item[
                        "top2_kb"
                    ]
                    output_email_split_sentence[key]["top3_kb"] = item[
                        "top3_kb"
                    ]
                    output_email_split_sentence[key]["top4_kb"] = item[
                        "top4_kb"
                    ]

            output_email_split_sentence[key]["extract_type"] = "split"

        output_email_split_sentence = list(
            output_email_split_sentence.values()
        )
        output_email_split_sentence = [
            {k: v for k, v in item.items() if k != "top1_simi"}
            for item in output_email_split_sentence
        ]

        # Update split info indices
        for data in email_split_info:
            num_org = data["extract_type_num"]
            data["extract_type_num"] = index_transform_dict.get(num_org, None)
            data["extract_type_num_org"] = num_org

        return output_email_split_sentence, email_split_info

    def _check_info_rewrite(
        self, email_split_info: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """Rewrite check info to final format.

        Args:
            email_split_info: Split info to rewrite.

        Returns:
            Tuple of (split_info, api_log).
        """
        split_info = []
        api_log = []

        for lst in email_split_info:
            split_info.append(
                {
                    "extract_type": lst["extract_type"],
                    "extract_type_num": lst["extract_type_num"],
                    "extract_type_num_org": lst["extract_type_num_org"],
                    "gpt_output_org": lst["gpt_output_org"],
                    "gpt_output": lst["gpt_output"],
                    "intent": lst["intent"],
                    "intent_similarity": lst["intent_similarity"],
                    "intent_key": lst["intent_key"],
                    "top1_kb": lst["top1_kb"],
                    "top1_kb_similarity": lst["top1_kb_similarity"],
                    "top1_kb_key": lst["key_1"],
                    "top2_kb": lst["top2_kb"],
                    "top2_kb_similarity": lst["top2_kb_similarity"],
                    "top2_kb_key": lst["key_2"],
                    "top3_kb": lst["top3_kb"],
                    "top3_kb_similarity": lst["top3_kb_similarity"],
                    "top3_kb_key": lst["key_3"],
                    "top4_kb": lst["top4_kb"],
                    "top4_kb_similarity": lst["top4_kb_similarity"],
                    "top4_kb_key": lst["key_4"],
                }
            )
            api_log.append(
                {
                    "extract_type": lst["extract_type"],
                    "extract_type_num": lst["extract_type_num_org"],
                    "api_log": lst.get("api_log", {}),
                }
            )

        return split_info, api_log

    @timed(task_name="email_detect_pipeline_run")
    async def run(
        self,
        case_id: str,
        product_type: str,
        product_model: str,
        problem_description_content: str,
        site: str,
        email_content: str,
    ) -> dict[str, Any]:
        """Run email detection pipeline.

        Args:
            case_id: Case identifier.
            product_type: Product type string.
            product_model: Product model string.
            problem_description_content: Problem description text.
            site: Website code.
            email_content: Full email content.

        Returns:
            Dictionary with detection results.
        """
        start_time_ts = int(time.time())

        # Prepare content
        if not problem_description_content:
            problem_description_content_new = email_content
            problem_description_content_new = re.sub(
                product_model, "", problem_description_content_new
            )
        else:
            problem_description_content_new = (
                "[Product Information]\n"
                f"Product Type: {product_type}\n\n"
                "[Problem Description]\n"
                f"{problem_description_content}"
            )

        # Find product line
        product_line = find_productline(site, product_type)
        self.product_line = product_line

        # Generate check info
        email_split_info, lang, summary = await self._generate_check_info(
            problem_description_content_new, product_line, site
        )

        # Extract GPT results
        gpt_extract = self._generate_gpt_extract(email_split_info)

        # Renumber
        gpt_extract, email_split_info = self._num_recode(
            gpt_extract, email_split_info
        )

        # Rewrite check info
        split_info, api_log = self._check_info_rewrite(email_split_info)

        end_time_ts = int(time.time())

        gpt_extract_type = (
            "unclear_description" if len(gpt_extract) == 0 else "available"
        )

        output = {
            "case_id": case_id,
            "gpt_extract": {
                "user_summary": summary,
                "type": gpt_extract_type,
                "email_split_sentence": gpt_extract,
            },
            "check_info": {
                "start_time_ts": start_time_ts,
                "end_time_ts": end_time_ts,
                "lang": lang,
                "product_line": product_line,
                "email_split_info": split_info,
            },
        }

        # Set extract log for middleware
        set_extract_log(
            {
                "api_call_info": api_log,
                "lang": lang,
                "product_line": product_line,
            }
        )

        return output
