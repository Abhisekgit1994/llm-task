import openai
import os
import re
import pandas as pd
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI


class LLMFunctions:
    def __init__(self):
        openai.api_key = "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"
        self.reference_schema = ResponseSchema(name="Reference_table_column", description="reference table column name")
        self.similar_col_schema = ResponseSchema(name="Candidate_table_similar_columns",
                                   description="for the column in reference table \
                                                extract most similar columns based on column name and value similarty and return the items in a list. \
                                                If you don't find any similar column return empty list.")
        self.reason_schema = ResponseSchema(name="Reason", description="Return the reason behind the similarity of the columns")
        self.response_schema_col = [self.reference_schema, self.similar_col_schema, self.reason_schema]

        self.code_schema = ResponseSchema(name='python_script', description='return python script as a string with indentation')
        self.output_schema = ResponseSchema(name='transformed_values', description='return the transformed values in a list')
        self.response_schema_code = [self.code_schema, self.output_schema]
        self.chat = ChatOpenAI(temperature=0.1)

        self.similar_col_prompt = """\
                                    For the following Reference table and Candidate table, perform tasks as instructed:
                                    Instruction:
                                    Reference_table_column: reference table column name
                                    
                                    Candidate_table_similar_columns: for the column in reference table \
                                    extract most similar columns strictly on same type and distribution of values for each candidate column data and return the items in a list. \
                                    check the value distribution for each candidate column while making decision.
                                    
                                    Reason: State the reason such as data type and value distribution behind the similarity and return as a string
                                    
                                    Reference table: {reference_table}
                                    Candidate table: {candidate_table}
                                    
                                    format the output as JSON with the following keys:
                                    Reference_table_column
                                    Candidate_table_similar_columns
                                    Reason
                                    """
        self.code_prompt = """\
                            For the following Reference list and Candidate list, perform tasks as instructed:
                            Instruction:
                            python_script: python script to transform data in candidate list \
                            to reference list items format
                            
                            transformed_values: apply the script to the candidate_list and replace the transformed_values in the response
                            
                            Reference list: {reference_list}
                            Candidate list: {candidate_list}
                            
                            {format_instructions_code}
                            
                            """

    def find_similar_columns(self, reference_table, candidate_table, col):
        """
        :param reference_table: reference table
        :param candidate_table: candidate table
        :param col: column in reference to find similar in candidate
        :return: output dict with Reference_table_column, Candidate_table_similar_columns, Reason as keys
        """

        output_parser = StructuredOutputParser.from_response_schemas(self.response_schema_col)
        # format_instructions = output_parser.get_format_instructions()
        prompt_template = ChatPromptTemplate.from_template(template=self.similar_col_prompt)
        messages = prompt_template.format_messages(candidate_table=candidate_table, reference_table=reference_table.head()[col])
        response = self.chat(messages)
        output_dict = output_parser.parse(response.content)
        return output_dict, response, messages

    def transform_values(self, reference_table, reference_col, candidate_table, candidate_col):
        """
        :param reference_table: template table data
        :param reference_col: access template table data of specific col
        :param candidate_table: candidate table data head
        :param candidate_col: specific column for candidate table data
        :return: output_dict with python code and transformed values
        """

        output_parser_code = StructuredOutputParser.from_response_schemas(self.response_schema_code)
        format_instructions_code = output_parser_code.get_format_instructions()
        prompt = ChatPromptTemplate.from_template(template=self.code_prompt)
        messages = prompt.format_messages(reference_list=reference_table[reference_col][:5].to_list(),
                                          candidate_list=candidate_table[candidate_col].to_list(), format_instructions_code=format_instructions_code)
        response = self.chat(messages)
        output_dict = output_parser_code.parse(response.content)
        return output_dict








