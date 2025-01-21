from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from typing import Optional, List, ClassVar, root_validator

from constants_and_maps import categories


CONTEXT_SETTING_PROMPT_TEMPLATES = {
    "Social": f"""
Purpose:  
The goal of this assistant is to analyze how video games influence social dynamics and interactions, including fostering communities, encouraging online collaboration, reducing social anxiety, and promoting inclusivity and diversity.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Social'])}
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Neuro/Cognitive": f"""
Purpose:  
The goal of this assistant is to evaluate how video games impact cognitive abilities, including memory, problem-solving, attention, and multitasking.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Neuro/Cognitive'])}
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Physiological": f"""
Purpose:  
The goal of this assistant is to examine the physical effects of video games, such as improvements in motor skills, reaction time, rehabilitation, and integration with health monitoring.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Physiological'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Psychological": f"""
Purpose:  
The goal of this assistant is to investigate the psychological effects of video games, including stress reduction, emotional regulation, therapy simulations, and their impact on aggression or mental health conditions.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Psychological'])}  
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Policy-making": f"""
Purpose:  
The goal of this assistant is to understand how video games influence or contribute to policy-making in various domains such as education, health, and environmental conservation.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Policy-making'])}   
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Governance": f"""
Purpose:  
The goal of this assistant is to explore how video games simulate or support governance-related activities such as crisis management, urban planning, and societal decision-making.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Governance'])}   
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Education": f"""
Purpose:  
The goal of this assistant is to analyze the role of video games in education, including STEM learning, medical training, and promoting critical thinking and creativity.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. Treat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Education'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Economics": f"""
Purpose:  
The goal of this assistant is to study the economic dimensions of video games, including virtual economies, real-world economic impact, and financial literacy gamification.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. Treat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Economics'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Ethical": f"""
Purpose:  
The goal of this assistant is to evaluate ethical considerations in video games, such as fairness, representation, privacy, and monetization practices.  

Rules:
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.  
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Ethical'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Sexualization": f"""
Purpose:  
The goal of this assistant is to investigate the portrayal of gender and sexualization in video games, including hypersexualized characters and cultural differences.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories:  {list(categories['Sexualization'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Addiction": f"""
Purpose:  
The goal of this assistant is to understand the patterns, strategies, and interventions related to video game addiction and overuse.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories:  {list(categories['Addiction'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Learning": f"""
Purpose:  
The goal of this assistant is to analyze how video games support learning through curriculum integration, puzzle solving, and collaborative methods.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Learning'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations or inferences.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Environmental": f"""
Purpose:  
The goal of this assistant is to examine the environmental themes and contributions of video games, including ecosystem simulations and renewable resource awareness.  

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Environmental'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Behavioral": f"""
Purpose:  
The goal of this assistant is to study player behavior influenced by video games, including altruism, risk-taking, and gambling-related issues.  Also identify what video game 

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Behavioral'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations.  
- Always aim to extract strategic insights, not just summarize the text.
""",
    "Technological": f"""
Purpose:  
The goal of this assistant is to explore technological innovations and applications in video games, including VR, AI, and game engine development. Also identify cases of using technology to make better games. 

Rules:  
- Correct formatting errors in input text; for example: The input text might have some text-formatting issues like '- ' (hyphen) separation within a given word. TReat it as a word when you see this.
- Classify the paper (input text) into one or more of the subcategories: {list(categories['Technological'])} 
- If it cannot be mapped to any of the above subcategories, classify it as "miscellaneous".
- Follow the detailed instructions below to extract the rest of the information according to the format given in the rest of the prompt and instructions.
- Be comprehensive while avoiding unsupported extrapolations.  
- Always aim to extract strategic insights, not just summarize the text.
"""
}


EXTRACT_INFORMATION_INSTRUCTIONS = """
        Using the complete set of instructions in the 'Detailed instructions for each field' document and generate a response in the given output format.
        Extract the following information fields: Issues, Demographics, Game names or products, Game classification, Game Attributes, Gamer Attributes, Game restrictions, Category of paper, Research methods, Conclusion.
        Guidelines for Game names or products, Game classification, Game Attributes and Game restrictions are in the 'Video Game Attributes' document.
        Follow the output format given, to return this response.
        Please write your response strictly in English. Do not use any other language."""


FINAL_PROMPT_TEMPLATES = """
        The input text to this prompt is information, organized into the same fields/categories from different parts of the same paper (example: introduction, methods, and conclusion).
        The role of this agent is to collate and summarize the information into the given format. Retain all the information given in the input. 
"""


class Paperwise_sectionwise_parser(BaseModel):
    """
    Structured output for client background queries, including analysis of themes, drivers, factors, benchmarks, touchpoints, and industry influences on reputation.
    """
    category: ClassVar[Optional[str]] = None  # Class-level variable to store 'category'

    Section: Optional[str] = Field(
        None,
        description="Section of the paper from which the information was extracted.",
    )
    Sub_category: Optional[str] = Field(
        None,
        description="""Comma-separated list of subcategories that the issue of the paper is classified as. 
        Always follow the rules given for classification into subcategories for the given category (set dynamically) to get this output.
        if not found, return 'NA'""",
    )

    @root_validator(pre=True)
    def dynamic_field_description(cls, values):
        """Dynamically update field behavior based on the category."""
        if cls.category:
            values['Sub_category'] = f"Relevant to category: {cls.category}"
        return values

    @classmethod
    def set_category(cls, category_value: str):
        """Sets the class-level category variable."""
        cls.category = category_value

    Game_name_or_product: Optional[str] = Field(
        None,
        description="""Identify the name of the game, gaming company or product from the input text. If not found, return 'None'.
        If the input text contains different game products or names, give all of them as comma separated strings.
        Always follow the description and process in the corresponding section of the ‘Detailed instructions for each field' to respond for 'Game names or products' only.""",
        max_length=200,
    )
    Game_category: Optional[str] = Field(
        None,
        description="""Identify the name of the game category or classification from the input text. If not found, return 'None'.
        If the input text contains different game categories, give all of them as comma separated strings.
        Always follow the description and process in the corresponding section of the ‘Detailed instructions for each field' to respond for 'Game Classification' only.
        Also use the description of 'Video Game genres' under the 'Video Game Attributes' section to follow the exact list of game categories to be stated.""",
        max_length=200,
    )
    Game_attributes: Optional[str] = Field(
        None,
        description="""Identify the game attributes from the input text following the guidelines for video game mechanics, dynamics and aesthetics. If not found, return 'None'.
        If the input text contains different game elements or attributes, give all of them as semi-colon separated strings.
        Always follow the description and process in the corresponding section of the ‘Detailed instructions for each field' to respond for 'Game Attributes' only.
        Also use the description of 'Video game elements' under the 'Video Game Attributes' section to follow the guidelines on game attributes to be stated.
        """,
        max_length=200,
    )
    Gamer_behavior_or_motivation: Optional[str] = Field(
        None,
        description="""Identify the gamer attributes from the input text. If not found, return 'None'.
        If the input text contains different gamer behavior attributes or motivation factors, give all of them as comma separated strings.
        Always follow the description and process in the corresponding section of the ‘Detailed instructions for each field' to respond for 'Gamer attributes' only.
        Also use the description of 'Gamer Behavior' under the 'Video Game Attributes' section to follow the guidelines on gamer motivation factors to be stated.
        """,
        max_length=200,
    )
    Game_restrictions: Optional[str] = Field(
        None,
        description="""Identify any game restrictions from the input text if present. If not found, return 'None'.
        If the input text contains different game restrictions, give all of them as comma separated strings.
        Always follow the description and process in the corresponding section of the ‘Detailed instructions for each field' to respond for 'Game restrictions' only.
        Also use the description of 'PEGI Ratings' under the 'Video Game Attributes' section to follow the guidelines on game restrictions to be stated.
        """,
        max_length=200,
    )
    Paper_category: Optional[str] = Field(
        None,
        description="""Classify the paper as Empirical, Theoterical or Computation on the basis of the content of the paper.
        Always follow the description and process in the corresponding section of the ‘Detailed instructions for each field' to respond for 'Category of paper' only.""",
        max_length=200,
    )
    Research_methods: Optional[str] = Field(
        None,
        description="""Identify and state any research methods stated in the paper.
        If none are found, state 'None'. If the input text contains different game restrictions, give all of them as comma separated strings.
        Always follow the description and process in the corresponding section of the ‘Detailed instructions for each field' to respond for 'Research Methods' only.        
        """,
        max_length=200,
    )
    conclusion: Optional[str] = Field(
        None,
        description="""Give a 2 line summary of the input text. The summary should contain the main problem being discussed in the text and how video games are relevant to this problem.
        """,
        max_length=200,
    )


class Total_Paper_Parser(BaseModel):
    Summaries: List[Paperwise_sectionwise_parser] = Field(
        description="List-wise summary of every section of paper covered in input context",
    )


OUTPUT_TEMPLATES = PydanticOutputParser(pydantic_object=Paperwise_sectionwise_parser),

