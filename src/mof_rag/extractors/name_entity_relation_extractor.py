import re
from pydantic import BaseModel, Field
from transformers import pipeline

from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.output import NativeOutput

class SynthesisProcedure(BaseModel):

    mof : str | None = None
    metal_source : str | None = None
    linker : str | None = None
    solvents : list | None = None
    temperature : dict | None = None
    time : dict | None = None

 

class Ner_Extractor:

    def __init__ (self):
        return

    
    def run(self):

        ner = pipeline(
            "ner",
            model="teman67/matscibert-chem-ner",
            aggregation_strategy="max",
            device="mps"
        )

        #text = """
        #    Zn(NO3)2·6H2O (0.297 g, 1 mmol) and H2BDC (0.166 g, 1 mmol) were dissolved 
        #    in DMF (15 mL). The mixture was heated at 120 °C for 48 h under solvothermal conditions.
        #    """

        text = """
        In a typical synthesis of MOF-5, Zn(NO3)2·6H2O (2.97 g, 10 mmol) and terephthalic acid (H2BDC, 0.83 g, 5 mmol) were dissolved in a mixed solvent system of N,N-dimethylformamide (DMF, 50 mL) and distilled water (5 mL). The resulting solution was sealed in a 100 mL Teflon-lined stainless steel autoclave and heated statically from room temperature to 105 °C at a ramp rate of 5 °C/min, maintaining this temperature for 72 h. After cooling to 25 °C naturally, colorless cubic crystals were filtered, washed three times with anhydrous DMF (3 x 15 mL), and subsequently activated under dynamic vacuum at 150 °C for 12 h to yield the final porous framework (yield: 78% based on Zn).
        """

        chemicals = ner(text)

        for entity in chemicals:
            print(f"{entity['word']:<30} {entity['entity_group']:<8} {entity['score']:.3f}")


        
        measurements = self.regex_unit_extractor(text, chemicals)
        print(measurements)


        relationships_output = self.run_agent(self.relationship_prompt(text, chemicals, measurements), ChemicalMeasurementOutput)

        reaction_conditions_output = self.run_agent(self.reaction_conditions_prompt(text, measurements), ReactionConditionsOutput)

        missed_entities_output = self.run_agent(self.missed_entities_prompts(text, chemicals, measurements, relationships_output, reaction_conditions_output), MissedEnitiesOutput)




        print("RELATIONSHIPS OUTPUT")
        print(relationships_output)
        print("\n")
        print("REACTION CONDITIONS OUTPUT")
        print(reaction_conditions_output)
        print("\n")
        print("MISSING OUTPUTS")
        print(missed_entities_output)

        return



    def regex_unit_extractor(self, text, identified_chemicals):

        chem_names = []
        for chem in identified_chemicals:
            chem_sep = [i.replace(" ", "") for i in chem["word"] if i is not None]
            chem_recon = "".join(chem_sep)
            if chem_recon:
                chem_names.append(chem_recon)

        masked_text = text
        for name in sorted(set(chem_names), key=len, reverse=True):
            masked_text = re.sub(
                re.escape(name), "[CHEMICAL]", masked_text, flags=re.IGNORECASE
            )

        print(masked_text)

        # 3. Extract all numbers and units from the clean masked text
        units = r"mg|g|kg|µg|mL|L|µL|mol|mmol|M|mM|°C|K|bar|atm|min|h|%"
        pattern = rf"(?<![a-zA-Z0-9.)\]])([-+]?\d+(?:\.\d+)?)\s*({units})(?![a-zA-Z])"

        found_units_list = re.finditer(pattern, masked_text, re.IGNORECASE)

        measurements = []
        for match in found_units_list:

            measurement = {
                "value": match.group(1),
                "unit": match.group(2),
                "start": match.start(),
                "end": match.end()
            }

            measurements.append(measurement)

        return measurements




    @staticmethod
    def relationship_prompt(text, chemicals, measurements):

        prompt = f"""
        You are an information extraction assistant specialising in materials chemistry and Metal-Organic Frameworks (MOFs).
        Extract all chemical-measurement relationships from the text below and return them inside the 'measurements' list.

        ORIGINAL TEXT:
        {text}

        PRE-EXTRACTED CHEMICAL ENTITIES:
        {chemicals}

        PRE-EXTRACTED MEASUREMENTS:
        {measurements}

        INSTRUCTIONS:
        - For every chemical compound mentioned, find its corresponding quantity and unit from the measurements list.
        - Include the exact quote from the text as 'evidence'.
        - You MUST populate the 'measurements' list with at least one item. Do not return an empty list.

        RULES:
        - Use the original text as your primary source of evidence.
        - Do not invent chemical compounds or measurements.
        """ 

        return prompt


    @staticmethod
    def reaction_conditions_prompt(text, measurements):
        prompt = f"""
        You are an expert materials chemistry assistant specialising in Metal-Organic Frameworks (MOFs).
        Extract all distinct reaction conditions from the text below and return them inside the 'reaction_conditions' list.

        ORIGINAL TEXT:
        {text}

        PRE-EXTRACTED MEASUREMENTS:
        {measurements}
        
        INSTRUCTIONS:
        - Break down the synthesis into chronologically distinct stages (e.g., primary reaction, cooling, post-synthetic activation).
        - For temperature and time, include BOTH the numeric value and the unit (e.g., temperature='105 °C', time='72 h'). Do not output just the unit.
        - **CRITICAL:** Only assign 'pressure' and 'vessel_spec' to the exact stage where they are explicitly mentioned. If a stage (like cooling or activation) does not use an autoclave or pressure vessel, leave those fields as 'Not specified' or 'N/A'. Do not smear global context across all rows.
        - Include the exact quote from the text as 'evidence'.
        - You MUST populate the 'reaction_conditions' list.

        RULES:
        - Use the original text as your primary source of evidence.
        - Do not invent reaction conditions.
        """ 
        return prompt



    @staticmethod
    def missed_entities_prompts(text, chemicals, measurements, chemicals_output, reaction_conditions_output):
        prompt = f"""
        You are an expert materials chemistry auditor specializing in Metal-Organic Frameworks (MOFs).
        Your task is to review the original text alongside the pre-extracted data and previous extraction results to find ANY entities or conditions that were missed.

        ORIGINAL TEXT:
        {text}

        PRE-EXTRACTED CHEMICAL ENTITIES (NER):
        {chemicals}

        PRE-EXTRACTED MEASUREMENTS (REGEX):
        {measurements}

        PREVIOUSLY EXTRACTED CHEMICAL MEASUREMENTS (PASS 1):
        {chemicals_output}

        PREVIOUSLY EXTRACTED REACTION CONDITIONS (PASS 2):
        {reaction_conditions_output}

        INSTRUCTIONS:
        - Audit the text against the previous extractions.
        - Identify any chemical compounds, precursors, solvents, or materials mentioned in the text that were completely missed. Return them in the 'missed_chemicals' list.
        - Identify any reaction conditions, thermal profiles (such as ramp rates or initial baseline temperatures), or vessel specs that were missed. Return them in the 'missed_reaction_conditions' list.
        - Identify any numerical measurements, volumes, times, or percentages that were missed by the regex or previous passes. Return them in the 'missed_measurements' list.
        - If nothing was missed in a category, return an empty list.

        RULES:
        - Rely only on clear facts directly mentioned in the text. Do not invent or hallucinate data.
        """

        return prompt


    
    def run_agent(self, prompt, output_type):

        model = OllamaModel("qwen3.6", provider=OllamaProvider(base_url='http://localhost:11434/v1'))
        agent = Agent(model, output_type=NativeOutput(output_type))

        print("PROMPT")
        print(prompt)

        result = agent.run_sync(prompt)


        return result.output



class ChemicalMeasurement(BaseModel):

    molecule: str = Field(description="Chemical name")
    quantity: float = Field(description="Numeric amount of the measurement")
    unit: str = Field(description="Unit of measurement")
    evidence: str = Field(description="Exact quotes to support the relationship")


class ReactionCondition(BaseModel):

    temperature: str = Field(description="Temperature of the reaction conditions")
    pressure: str = Field(description="Pressure of the reaction, if specified")
    time: str = Field(description="Length of time the reaction takes place")
    vessel_spec: str = Field(description="Specification of vessels used")
    evidence: str = Field(description="Exact quotes to support the relationship")



class ChemicalMeasurementOutput(BaseModel):
    measurements: list[ChemicalMeasurement] = Field(
        default_factory=list,
        description="List of Extracted chemical-measurement relationships."
    )    


class ReactionConditionsOutput(BaseModel):
    reaction_conditions: list[ReactionCondition] = Field(
        default_factory=list,
        description="List of reaction conditions"
    )


class MissedEnitiesOutput(BaseModel):
    missed_chemicals: list[str] = Field(
        default_factory= list,
        description="Any chemicals that are observed but missed by named entity relation model"
    )

    missed_reaction_conditions: list[str] = Field(
        default_factory=list,
        description="Any reaction conditions that are observed but missed"
    )

    missed_measurements: list[str] = Field(
        default_factory=list, 
        description="Any measurements that are observed but missed by regex."
    )





ner_extractor = Ner_Extractor()
ner_extractor.run()