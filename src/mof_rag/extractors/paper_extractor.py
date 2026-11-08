import os

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser


class PaperExtractor:
    def __init__ (self, settings):
        marker_settings = settings.model_dump()

        config_parser = ConfigParser(marker_settings)

        self.converter = PdfConverter(
            config= config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service()
        )


    def extract(self, pdf_path):
        document = self.converter.build_document(pdf_path)
        blocks = document.contained_blocks()

        return blocks, document

