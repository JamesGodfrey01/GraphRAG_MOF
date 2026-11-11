import re

from bs4 import BeautifulSoup

from pylatexenc.latex2text import LatexNodes2Text

from marker.schema import BlockTypes




class SectionProcessor:

    def __init__ (self, blocks, document):
        self.blocks = blocks
        self.document = document

        self.sections = []
        self.captions = []
        self.tables = []



    def process_blocks(self):

        self.sections = []
        self.captions = []
        self.tables = []

        current_section = None

        for block in self.blocks:

            # Ignore PageFooters
            if block.block_type == BlockTypes.PageFooter:
                print(f"REMOVING FOOTER, {block}\n")
                continue


            elif block.block_type == BlockTypes.SectionHeader:
                current_section = {
                    "heading": block.raw_text(self.document).strip(),
                    "paragraphs": []
                }
                self.sections.append(current_section)
        
        
            elif block.block_type == BlockTypes.Table:
                self.tables.append(block)

            elif block.block_type == BlockTypes.Caption:
                self.captions.append(block)


            elif block.block_type == BlockTypes.Text:
                if current_section is not None:
                    text = block.raw_text(self.document)
                    if text and text.strip():
                        cleaned_text = text.strip()
                        current_section["paragraphs"].append(cleaned_text)


            


        return {
            "sections": self.sections,
            "captions": self.captions,
            "tables": self.tables
        }



    @staticmethod
    def strip_html(text):

        soup = BeautifulSoup(text, 'html.parser')

        return soup.get_text(separator=" ")



    def sections_html_strip(self, results):

        for section in results["sections"]:
            # Clean heading
            section["heading"] = self.strip_html(
                text= section["heading"]
            )
            

            section["paragraphs"] = [
                self.strip_html(paragraph)
                for paragraph in section["paragraphs"]
            ]

        return results



    def captions_html_strip(self, results):
        
        results["captions"] = [
            self.strip_html(caption.raw_text(self.document))
            for caption in results["captions"]
        ]
        return results



    def tables_html_strip(self, results):

        results["tables"] = [
            self.strip_html(table.raw_text(self.document))
            for table in results["tables"]
        ]
        return results


    def separate_table_and_figure_captions(self, results):

        # instantiate empty table_captions and figure_captions lists in results
        results["table_captions"] = []
        results["figure_captions"] = []

        for caption in results["captions"]:
            caption = caption.lower()

            if caption.startswith("table"):
                results["table_captions"].append(caption)

            
            elif re.search(pattern=r"table \d+", string=caption, flags=re.IGNORECASE):
                results["table_captions"].append(caption)

            else:
                results["figure_captions"].append(caption)

        return results


    @staticmethod
    def sections_convert_latex(results, latex_converter):

        for section in results["sections"]:

            section["heading"] = latex_converter.latex_to_text(section["heading"])
            
            section["paragraphs"] = [
                latex_converter.latex_to_text(paragraph)
                for paragraph in section["paragraphs"]
            ]

        return results


    @staticmethod
    def captions_convert_latex(results, latex_converter):

        results["captions"] = [
            latex_converter.latex_to_text(caption)
            for caption in results["captions"]
        ]

        return results



    @staticmethod
    def tables_convert_latex(results, latex_converter):

        results["tables"] = [
            latex_converter.latex_to_text(table)
            for table in results["tables"]
        ]

        return results


    
    @staticmethod
    def convert_underscores_to_subscripts(text):
    
        subscript_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        
        # Find any underscore followed by one or more digits anywhere in the text
        # and translate those digits into subscripts.
        return re.sub(r'_([0-9]+)', lambda m: m.group(1).translate(subscript_map), text)



    def apply_underscores_to_subscripts(self, results):


        for key, _ in results.items():

            if key == "sections":
                for section in results["sections"]:
                    if section.get("heading"):
                        section["heading"] = self.convert_underscores_to_subscripts(section["heading"])

                    if section.get("paragraphs"):
                        section["paragraphs"] = [
                            self.convert_underscores_to_subscripts(text) for text in section["paragraphs"]
                        ]

            elif key in ["captions", "tables"]:

                results[key]= [self.convert_underscores_to_subscripts(text) for text in results[key]]


        return results



    @staticmethod
    def identify_references(results):

        # Match reference numbering formats:
        reference_start_pattern = re.compile(
            r"^\s*(?:\[\d+\]|\d+[.)]?)(?=\s)"
        )

        # Match publication years from 1900–2099
        year_pattern = re.compile(r"\b(?:19|20)\d{2}\b")

        # Match references marked as unpublished
        unpublished_pattern = re.compile(
            r"\bunpublished\b", re.IGNORECASE
        )

        references = []

        for section in results.get("sections", []):

            heading = section.get("heading", "").strip().lower()


            remaining_paragraphs = []

            for paragraph in section.get("paragraphs", []):

                if not isinstance(paragraph, str):
                    remaining_paragraphs.append(paragraph)
                    continue

                paragraph = paragraph.strip()

                has_number = bool(
                    reference_start_pattern.match(paragraph)
                )

                has_year = bool(
                    year_pattern.search(paragraph)
                )

                is_unpublished = bool(
                    unpublished_pattern.search(paragraph)
                )

                # Check for capitalised author names or initials
                has_capitals = bool(
                    re.search(r"\b[A-Z][a-z]+|\b[A-Z]\.", paragraph)
                )


                # Require numbering and either a year or unpublished marker.
                # Capitalisation is an additional supporting feature.
                if (
                    has_number
                    and (has_year or is_unpublished)
                    and has_capitals
                ):
                    references.append(paragraph)
                    print(f"Reference detected and moved:\n{paragraph}\n\n")

                else:
                    remaining_paragraphs.append(paragraph)

            section["paragraphs"] = remaining_paragraphs

        return references, results




    @staticmethod
    def remove_heading_words(text):

        if not text or not text.strip():
            return ""

        header_removal_words = [
            "view article online",
            "published on",
            "downloaded by",
            "http://",
            "https://"
        ]

        sentences = re.split(r'(?<=[.!?])\s+', text)

        cleaned_sentences = []

        for sentence in sentences:

            sentence_lower = sentence.lower()

            if any(word in sentence_lower for word in header_removal_words):
                print(f"Removing boilerplate sentence:\n{sentence}")

            else:
                cleaned_sentences.append(sentence)

        reconstructed = " ".join(cleaned_sentences).strip()

        return reconstructed if reconstructed else ""



    def apply_remove_header_words(self, results):

        for key in results.keys():

            if key == "sections":

                for section in results["sections"]:

                    if section.get("heading"):
                        section["heading"] = self.remove_heading_words(
                            section["heading"]
                        )

                    if section.get("paragraphs"):
                        section["paragraphs"] = [
                            cleaned_text
                            for text in section["paragraphs"]
                            if (cleaned_text := self.remove_heading_words(text))
                        ]

            elif key in ["captions", "tables"]:

                results[key] = [
                    cleaned_text
                    for text in results[key]
                    if (cleaned_text := self.remove_heading_words(text))
                ]

        return results









    def concat_span_data_types(self, blocks):

        end_of_doc_span = []
        for b in blocks:
            if b.block_type not in (BlockTypes.Span, BlockTypes.ListItem, BlockTypes.Line):
                end_of_doc_span.append("BREAKBREAK")

            if b.block_type in (BlockTypes.Span, BlockTypes.ListItem, BlockTypes.Line):
                end_of_doc_span.append(b.text)


        doc_span_clean = []
        prev = None

        for cur in end_of_doc_span:
            if cur == "BREAKBREAK" and prev == "BREAKBREAK":
                continue

            doc_span_clean.append(cur)
            prev = cur


        doc_span_joined= " ".join(doc_span_clean).split(sep="BREAKBREAK")
        doc_span_joined = [i.strip() for i in doc_span_joined]
        doc_span_joined = [i.replace("\n", "") for i in doc_span_joined]
        doc_span_joined = [i.replace("  ", " ") for i in doc_span_joined]
        doc_span_joined = [i.replace("   ", " ") for i in doc_span_joined]

        return doc_span_joined








    
    def extract(self):

        # Initial split of blocks. Useful to use html for separating into paragraphs, hence before the html clean.
        results = self.process_blocks()

        # Cleans the sections and its correspondinf text
        results = self.sections_html_strip(
            results= results
        )

        # Captions include Figure captions and Table captions
        results = self.captions_html_strip(
            results= results
        )

        # This is the table content only
        results = self.tables_html_strip(
            results= results
        )

        # Clean mathematical latex notation to usable format
        results = self.sections_convert_latex(
            results= results,
            latex_converter = LatexNodes2Text() 
        )

        results = self.captions_convert_latex(
            results= results,
            latex_converter = LatexNodes2Text()
        )

        results = self.tables_convert_latex(
            results= results,
            latex_converter = LatexNodes2Text()
        )


        results = self.apply_underscores_to_subscripts(
            results= results
        )

        results = self.apply_remove_header_words(
            results= results
        )


        # separate Table captions and Figure Captions
        results = self.separate_table_and_figure_captions(
            results= results
        )

        return results
