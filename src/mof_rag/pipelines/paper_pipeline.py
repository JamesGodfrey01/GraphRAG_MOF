import os

from mof_rag.cache.cache import PaperCache
from mof_rag.extractors.paper_extractor import PaperExtractor
from mof_rag.config.settings import Settings, ExtractorSettings
from mof_rag.processors.section_processor import SectionProcessor


class PaperPipeline:

    def __init__(self,
                 settings: Settings,
                 extractor_settings: ExtractorSettings
    ):


        self.settings = settings

        self.extractor_settings = extractor_settings

        self.paper_cache = PaperCache(
            cache_dir = self.settings.marker_cache_dir
        )

        self.paper_extractor = PaperExtractor(
            settings= self.extractor_settings
        )



    def run(self):
        os.environ["OPENAI_TIMEOUT"] = "1000" 

        # Test on one file for simplicity first
        INPUT_FILE = "/Users/jamesgodfrey/Documents/Code/knowledgegraphRAG/data/test/a-domenicano-the-crystal-structure-of-a-2-1-complex-of.pdf"


        # Get cache or extract document

        cache = self.paper_cache.get_cache(input_file=INPUT_FILE)

        if cache is None:

            print("No cached file found: "
                  f"{self.paper_cache.get_filename(INPUT_FILE)}"
            )


            blocks, document = self.paper_extractor.extract(
                pdf_path= INPUT_FILE
            )

            # Now save the extracted to cache
            self.paper_cache.save_cache(
                document=document,
                input_file= INPUT_FILE
            )

        else:

            print(f"Found cached file:"
                  f"{self.paper_cache.get_filename(INPUT_FILE)}"
            )

            blocks, document = cache



        # Process sections

        section_processor = SectionProcessor(
            blocks= blocks,
            document= document
        )

        results = section_processor.extract()


        # Identify references

        references, results = section_processor.identify_references(results= results)

        span_data_joined = section_processor.concat_span_data_types(blocks= blocks)


        span_data = [
            cleaned_text
            for text in span_data_joined
            if (cleaned_text := section_processor.remove_heading_words(text))
        ]


        return {"results": results,
                "references": references,
                "span": span_data
        }




settings = Settings()
extractor_settings = ExtractorSettings()

paper_pipeline = PaperPipeline(
    settings=settings,
    extractor_settings=extractor_settings
)
res = paper_pipeline.run()




