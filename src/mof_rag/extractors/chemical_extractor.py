import re
from pydantic import BaseModel, Field
from transformers import pipeline

from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.output import NativeOutput
import os
from typing import Literal
from dataclasses import dataclass

os.environ["PYDANTIC_AI_NO_BANNER"] = "1"



class SynthesisLinker:
    def __init__ (self):

        self.ner = pipeline(
            "ner",
            model="teman67/matscibert-chem-ner",
            aggregation_strategy='max',
            #ignore_labels = [],
            device="mps"
        )

        self.model = OllamaModel("qwen3.6", provider=OllamaProvider(base_url='http://localhost:11434/v1'))

        self.agent = Agent(self.model, output_type=NativeOutput(ChemicalMeasurementsOutput),
            instructions=chemical_measurement_linking_prompt(),
            deps_type=LinkingDeps,
            model_settings={"temperature": 0})


        return


    def run(self):

        """
        Water fails to be picked up by NER. do Water -> H2O
        """

    

        text = """
        In a typical synthesis of MOF-5, Zn(NO3)2·6H2O (2.97 g, 10 mmol) and terephthalic acid (H2BDC, 0.83 g, 5 mmol) were 
        dissolved in a mixed solvent system of N,N-dimethylformamide (DMF, 50 mL) and distilled water (5 mL). 
        The resulting solution was sealed in a 100 mL Teflon-lined stainless steel autoclave and heated statically from 
        room temperature to 105 °C at a ramp rate of 5 °C/min, maintaining this temperature for 72 h. After cooling to 25 °C 
        naturally, colorless cubic crystals were filtered, washed three times with anhydrous DMF (3 x 15 mL), and subsequently 
        activated under dynamic vacuum at 150 °C for 12 h to yield the final porous framework (yield: 78% based on Zn).
        """


        chemicals = self.ner(text)
        chemicals = self.merge_adjacent_named_entity_relationship_spans(chemicals, text)

        quantites_and_units = self.regex_quantity_and_unit_extractor(chemicals, text)


        text_tagged = self.insert_chemical_and_quantity_tags(chemicals, quantites_and_units, text)

        
        acceptable_chemical_ids = set(c['id'] for c in chemicals)
        acceptable_quantities_units_ids = set(q['id'] for q in quantites_and_units)
        

        print("CALLING AGENT:")

        result = self.agent.run_sync(
            f"PARAGRAPH:\n{text_tagged}",
            deps=LinkingDeps(acceptable_chemical_ids, acceptable_quantities_units_ids),
        )

        print("TAGGED TEXT:")
        print(text_tagged)


        print("\nAGENT OUTPUT:\n")

        print(result)


    def insert_chemical_and_quantity_tags(self, chemicals, quantities_and_units, text):


        merged_chemicals_and_quantities_and_units = quantities_and_units + chemicals

        merged_chemicals_and_quantities_and_units_sorted_backwards = sorted(merged_chemicals_and_quantities_and_units, key=lambda x: x['end'], reverse=True)

        for i in merged_chemicals_and_quantities_and_units_sorted_backwards:

            tag = '{' + str(i['id']) + '}'
            text_left_and_entity= text[:i['end']]
            text_right_q = text[i['end']:]

            text = text_left_and_entity + tag + text_right_q

        return text





    def regex_quantity_and_unit_extractor(self, chemicals, text):

        # Mask the chemicals based on the chemicals[['start','end']]
        text_masked_of_chemicals = self.mask_chemicals_in_text(chemicals, text)


        rates = r"°C\s*/\s*min|°C\s*min-1|°C\s*min−1|°C\s*min⁻¹|K\s*/\s*min|K\s*min-1|°C\s*/\s*h|mL\s*/\s*min|mL\s*min-1|rpm"
        units = rf"{rates}|mg|g|kg|µg|μg|mL|L|µL|μL|mmol|µmol|μmol|mol|mM|M|°C|K|bar|atm|min|h|%"

        pattern = rf"(?<![a-zA-Z0-9.)\]])([-+]?\d+(?:\.\d+)?)\s*({units})(?![a-zA-Z])"

        found_units = re.finditer(pattern, text_masked_of_chemicals)


        quantites_and_units = []
        for idx, q in enumerate(found_units):

            _quant = {
                'value': float(q.group(1)),
                'unit': q.group(2),
                'start': int(q.start()),
                'end': int(q.end()),
                'id': "Q_" + str(idx)
            }

            quantites_and_units.append(_quant)


        return quantites_and_units



    @staticmethod
    def mask_chemicals_in_text(chemicals, text):

        """
        Returns a text masked of its chemicals based on the index values.

        Length of the full input text is the same as the length of the output masked text
        """

        reverse_sorted_chemicals = sorted(chemicals, key= lambda x: x['end'], reverse= True)

        for chem in reverse_sorted_chemicals:
            text_left = text[:chem['start']]
            text_right = text[chem['end']:]

            text = text_left + f"{'#' * (chem['end'] - chem['start'])}" + text_right
            
        return text



    @staticmethod
    def merge_adjacent_named_entity_relationship_spans(chemicals, text):

        chemicals = sorted(chemicals, key= lambda x: x['start'])
        #print(chemicals)
    
        concat_adj_chemicals = []
        for entity in chemicals:

            if not concat_adj_chemicals or entity['start'] > concat_adj_chemicals[-1]['end']:

                _chem = {
                    "start": entity["start"],
                    "end": entity["end"],
                    "score": entity["score"]
                }

                concat_adj_chemicals.append(_chem)

            else:

                prev_start = concat_adj_chemicals[-1]['start']
                prev_end= concat_adj_chemicals[-1]['end']
                prev_score = concat_adj_chemicals[-1]['score']

                _chem = {
                    "start": prev_start,
                    "end": max(entity['end'], prev_end),
                    "score": min(entity['score'], prev_score),
                }

                concat_adj_chemicals[-1] = _chem

        for chem in concat_adj_chemicals:
            chem['name'] = text[chem['start']: chem['end']]


        for idx, chem in enumerate(concat_adj_chemicals):
            chem['id'] = "E_" + str(idx)


        print(concat_adj_chemicals)

        return concat_adj_chemicals






ChemicalRole = Literal[
    'metal_source',
    'linker',
    'solvent',
    'modulator',
    'base',
    'additive',
    'other'
]

SynthesisType = Literal[
    'reaction',
    'cooling',
    'washing',
    'activation',
    'solvent_exchange',
    'filtering',
    'other'
]

StepCondition = Literal[
    'temperature',
    'pressure',
    'duration',
    'vessel_volume',
    'stirring_speed',
    'ramp_rate',
    'other'
]




@dataclass
class LinkingDeps:
    acceptable_chemical_ids: set[str]
    acceptable_quantities_units_ids: set[str]


class ChemicalMeasurement(BaseModel):
    chemical_id : str = Field(description= "Chemical id tag. For example 'E_0'")
    quantity_ids : list[str] = Field(description= "Quantity tags that are amounts of THIS chemical. For example ['Q_0', 'Q_1']. Empty if the text gives no amount")

    role: ChemicalRole = Field(description="What the chemical does in this synthesis step")
    synthesis_type: SynthesisType = Field(description="Which step does this chemical belong to")


class Condition(BaseModel):
    quantity_id : str = Field(description="Quantity tag. For example 'Q_4'")
    condition_type : StepCondition = Field(description="What the quantity describes")
    synthesis_type : SynthesisType = Field(description="Which step does this condition belong to")


class Product(BaseModel):
    chemical_id : str = Field(description="Tag of the material this synthesis makes. For example 'E_0'")
    yield_quantity_id : str | None = Field(default=None, description="Quantity tag of the reported yield, if any. For example 'Q_14'")


class ChemicalMeasurementsOutput(BaseModel):
    product : Product | None = Field(default=None, description="The material this synthesis makes. None if the product is not named or tagged")
    chemical_measurements : list[ChemicalMeasurement] = Field(default_factory= list, description= "Every chemical that takes part in the synthesis. The same chemical used in two steps appears twice.")
    conditions : list[Condition] = Field(default_factory= list, description= "Every quantity that is a condition (temperature, duration, ...) rather than a chemical amount.")






def chemical_measurement_linking_prompt():

    prompt = """\
    You extract synthesis information from Metal-Organic Framework (MOF) papers.

    INPUT FORMAT
    The paragraph has been pre-tagged:
    - {E_n} directly after a chemical name, e.g. "Zn(NO3)2·6H2O{E_1}"
    - {Q_n} directly after a quantity and its unit, e.g. "2.97 g{Q_0}"

    OUTPUT IDS
    - Every chemical_id must be an E tag exactly as written, e.g. "E_1".
    - Every quantity ID must be a Q tag exactly as written, e.g. "Q_0".
    - Never write chemical names, units or numbers in ID fields.
    - Never invent an ID that is not in the paragraph.

    TASK
    Put every quantity tag into exactly one of these:
    1. An amount of a chemical -> add it to that chemical's quantity_ids.
    2. A condition of a step (temperature, duration, ramp_rate, pressure,
       stirring_speed, vessel_volume) -> add it to conditions.
    3. The yield of the product -> product.yield_quantity_id.
    4. Neither -> leave it out.
    Each quantity ID may be used at most once.

    PRODUCT
    - The material being synthesised (e.g. "MOF-5", "ZIF-8") goes in product,
      NOT in chemical_measurements.
    - If the product has no tag, set product to null.

    CHEMICALS
    - Include a chemical only if it is added or used during the synthesis.
    - Leave out vessel materials (e.g. "Teflon") and chemicals only mentioned in
      passing (e.g. "yield based on Zn").
    - If a chemical is named and then abbreviated in brackets, e.g.
      "terephthalic acid{E_2} (H2BDC{E_3}", use only the first ID (E_2).
    - If the same chemical is used in two steps (e.g. DMF as the reaction solvent
      and again for washing), list it twice, once per step.
    - A chemical with no amount in the text gets an empty quantity_ids list.

    LINKING QUANTITIES
    - A quantity belongs to the chemical it directly follows, usually in brackets.
    - If a quantity follows a chemical name that has no tag, leave the quantity
      out. Do not give it to a nearby chemical.

    ROLES
    - metal_source: provides the metal ions (metal salts, oxides)
    - linker: the organic ligand that bridges metal centres in the framework
    - solvent: the liquid the reaction or a later step takes place in
    - modulator: acid or monotopic ligand added to control crystal growth
      (e.g. acetic acid, benzoic acid, HCl)
    - base: added to deprotonate the linker (e.g. triethylamine, NaOH)
    - additive: anything else deliberately added (surfactants, templates)
    - other: none of the above fits

    STEPS
    reaction (mixing and heating), cooling, filtering, washing,
    solvent_exchange, activation (heat or vacuum to empty the pores), other.

    EXAMPLE
    Paragraph:
    Zn(NO3)2·6H2O{E_0} (0.30 g{Q_0}) and 2-methylimidazole{E_1} (0.66 g{Q_1})
    were dissolved in methanol{E_2} (20 mL{Q_2}) and stirred at 25 °C{Q_3}
    for 24 h{Q_4} to give ZIF-8{E_3}.

    Output:
    {"product": {"chemical_id": "E_3", "yield_quantity_id": null},
     "chemical_measurements": [
       {"chemical_id": "E_0", "quantity_ids": ["Q_0"], "role": "metal_source", "synthesis_type": "reaction"},
       {"chemical_id": "E_1", "quantity_ids": ["Q_1"], "role": "linker", "synthesis_type": "reaction"},
       {"chemical_id": "E_2", "quantity_ids": ["Q_2"], "role": "solvent", "synthesis_type": "reaction"}],
     "conditions": [
       {"quantity_id": "Q_3", "condition_type": "temperature", "synthesis_type": "reaction"},
       {"quantity_id": "Q_4", "condition_type": "duration", "synthesis_type": "reaction"}]}

    If something is genuinely unclear, choose "other" rather than guessing.
    """

    return prompt



if __name__ == "__main__":
    sl = SynthesisLinker()
    sl.run()