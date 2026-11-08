from pathlib import Path
import sys
import gemmi
import json
import pandas as pd

from mof_rag.config.settings import Settings

settings = Settings()


class CifExtractor:

    def __init__(self):
        self.paper_tracking = pd.read_csv(settings.paper_tracking_csv)



    def parse_cif_value_and_uncertainty(self, val_str):
        """
        Parses raw CIF values such as:
            '106.79(5)'
            '106.79'
            '15'
            '?'
            ['106.79(5)', '107.12(4)']

        Returns:
            (value, uncertainty) for a single value, or
            (values, uncertainties) for a list.
        """

        if val_str is None or val_str in ('?', '.'):
            return None, None


        # Handle lists recursively
        if isinstance(val_str, list):
            values = []
            uncertainties = []

            for item in val_str:
                value, uncertainty = self.parse_cif_value_and_uncertainty(item)
                values.append(value)
                uncertainties.append(uncertainty)

            return values, uncertainties


        val_str = str(val_str).strip()

        # No uncertainty reported
        if '(' not in val_str:
            return float(val_str), None

        # Contains uncertainty
        main_val_str, unc_str = val_str.replace(')', '').split('(')

        if '.' in main_val_str:
            decimal_places = len(main_val_str.split(".")[1])
        else:
            decimal_places = 0

        uncertainty = int(unc_str) / (10 ** decimal_places)

        return float(main_val_str), uncertainty



    def get_paper_title(self, mof_code):

        fpath = self.paper_tracking[
            self.paper_tracking['ccdc_id'] == mof_code.upper()
        ]['file_path']

        title = fpath.iloc[0]


        return title.replace('papers/', '')





    def cif_to_dict(self, cif_file_path):

        print(cif_file_path)

        doc = gemmi.cif.read_file(str(Path(cif_file_path)))

        json_str = doc.as_json()
        d = json.loads(json_str)


        # Extract CIF

        # Get the first MOF entry in dictionary 'd'
        mof_code = next(iter(d))

        # Cell Volume & Formula Units
        cell_volume, cell_volume_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code].get('_cell_volume'))
        cell_formula_units_z = d[mof_code].get('_cell_formula_units_z')

        # Chemical
        chemical_formula = d[mof_code].get('_chemical_formula_moiety')
        chemical_name_systematic = d[mof_code].get('_chemical_name_systematic')

        # Symmetry
        symmetry_cell_setting = d[mof_code].get('_symmetry_cell_setting')
        symmetry_space_group_name_h_m = d[mof_code].get('_symmetry_space_group_name_h-m')

        symmetry_equiv_pos_site_id = d[mof_code].get('_symmetry_equiv_pos_site_id', [])
        symmetry_equiv_pos_as_xyz = d[mof_code].get('_symmetry_equiv_pos_as_xyz', [])

        symmetry_operations = [
            {
                "id": site_id,
                "operation": operation
            }
            for site_id, operation in zip(
                symmetry_equiv_pos_site_id,
                symmetry_equiv_pos_as_xyz
            )
        ]

        # Cell lengths
        cell_length_a, cell_length_a_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code].get('_cell_length_a'))
        cell_length_b, cell_length_b_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code].get('_cell_length_b'))
        cell_length_c, cell_length_c_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code].get('_cell_length_c'))

        # Cell angles
        cell_angle_alpha, cell_angle_alpha_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code].get('_cell_angle_alpha'))
        cell_angle_beta, cell_angle_beta_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code].get('_cell_angle_beta'))
        cell_angle_gamma, cell_angle_gamma_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code].get('_cell_angle_gamma'))

        # Atoms
        atom_site_label = d[mof_code]['_atom_site_label']
        atom_site_type_symbol = d[mof_code]['_atom_site_type_symbol']
        atom_site_fract_x, atom_site_fract_x_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code]['_atom_site_fract_x'])
        atom_site_fract_y, atom_site_fract_y_uncertainty= self.parse_cif_value_and_uncertainty(d[mof_code]['_atom_site_fract_y'])
        atom_site_fract_z, atom_site_fract_z_uncertainty = self.parse_cif_value_and_uncertainty(d[mof_code]['_atom_site_fract_z'])


        atoms_zipped = zip(
            atom_site_label,
            atom_site_type_symbol,
            atom_site_fract_x,
            atom_site_fract_y,
            atom_site_fract_z,
            atom_site_fract_x_uncertainty,
            atom_site_fract_y_uncertainty,
            atom_site_fract_z_uncertainty
            )



        cell = gemmi.UnitCell(
            float(cell_length_a),
            float(cell_length_b),
            float(cell_length_c),
            float(cell_angle_alpha),
            float(cell_angle_beta),
            float(cell_angle_gamma)
        )
        
        
        atoms = []
        
        for label, element, x, y, z, x_unc, y_unc, z_unc in atoms_zipped:

            # Fractional coordinates
            frac = gemmi.Fractional(
                float(x),
                float(y),
                float(z)
            )
        
            # Convert to Cartesian Angstrom coordinates
            cart = cell.orthogonalize(frac)
        
            atoms.append(
                {
                    "label": label,
                    "element": element,
        
                    "fractional_coordinates": {
                        "x": float(x),
                        "y": float(y),
                        "z": float(z)
                    },
        
                    "cartesian_coordinates": {
                        "x": round(cart.x, 4),
                        "y": round(cart.y, 4),
                        "z": round(cart.z, 4),
                        "unit": "angstrom"
                    },

                    "uncertainty": {
                        "x": x_unc,
                        "y": y_unc,
                        "z": z_unc
                    }
                }
            )

        # Bonds
        geom_bond_atom_site_label_1 = d[mof_code].get('_geom_bond_atom_site_label_1', [])
        geom_bond_atom_site_label_2 = d[mof_code].get('_geom_bond_atom_site_label_2', [])
        geom_bond_site_symmetry_1 = d[mof_code].get('_geom_bond_site_symmetry_1', [])
        geom_bond_site_symmetry_2 = d[mof_code].get('_geom_bond_site_symmetry_2', [])

        bonds = [
            {
                "atom_1": atom_1,
                "atom_2": atom_2,
                "symmetry": {
                    "atom_1": symmetry_1,
                    "atom_2": symmetry_2
                }
            }
            for atom_1, symmetry_1, atom_2, symmetry_2 in zip(
                geom_bond_atom_site_label_1,
                geom_bond_site_symmetry_1,
                geom_bond_atom_site_label_2,
                geom_bond_site_symmetry_2
            )
        ]


        print(self.get_paper_title(mof_code))


        # Construct data dict 
        mof_data = {
            "mof_code": mof_code,
            "chemical": {
                "formula": chemical_formula,
                "name_systematic": chemical_name_systematic
            },
            "cell": {
                "length_a": cell_length_a,
                "length_a_uncertainty": cell_length_a_uncertainty,
                "length_b": cell_length_b,
                "length_b_uncertainty": cell_length_b_uncertainty,
                "length_c": cell_length_c,
                "length_c_uncertainty": cell_length_c_uncertainty,
                "angle_alpha": cell_angle_alpha,
                "angle_alpha_uncertainty": cell_angle_alpha_uncertainty,
                "angle_beta": cell_angle_beta,
                "angle_beta_uncertainty": cell_angle_beta_uncertainty,
                "angle_gamma": cell_angle_gamma,
                "angle_gamma_uncertainty": cell_angle_gamma_uncertainty,
                "volume": cell_volume,
                "formula_units_z": cell_formula_units_z,
                "volume_uncertainty": cell_volume_uncertainty
            },
            "symmetry": {
                "cell_setting": symmetry_cell_setting,
                "space_group_h_m": symmetry_space_group_name_h_m,
                "operations": symmetry_operations
            },
            "atoms": atoms,
            "bonds": bonds,
            "paper": self.get_paper_title(mof_code)
        }

        return mof_data, mof_code



    def main(self):
        OUTPUT_DIR = settings.mof_json_dir

        for cif_file in Path(settings.ready_cif_dir).glob("*.cif"):


            mof_data, mof_code = self.cif_to_dict(cif_file)


            with open(OUTPUT_DIR / f'{mof_code}.json', 'w', encoding='utf-8') as json_file:
                json.dump(mof_data, json_file, indent=4)



if __name__ == "__main__":
    cif_extractor = CifExtractor()
    cif_extractor.main()
