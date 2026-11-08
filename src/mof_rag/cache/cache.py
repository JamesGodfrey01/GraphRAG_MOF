from pathlib import Path
import cloudpickle



class PaperCache:
    def __init__ (self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


    @staticmethod
    def get_filename(input_file):
        return Path(input_file).stem


    def cache_exists(self, filename):
        cache_file= self.cache_dir / f"{filename}.pkl"
        
        return cache_file.exists()



    def load_cache(self, filename):

        load_filename = self.cache_dir / f"{filename}.pkl"
        with open(load_filename, "rb") as f:
            document = cloudpickle.load(f)

        blocks = document.contained_blocks()

        return blocks, document



    def get_cache(self, input_file):
        filename = self.get_filename(input_file= input_file)

        if self.cache_exists(filename= filename):

            blocks, document = self.load_cache(filename= filename)

            return blocks, document

        else:
            return None



    def save_cache(self, document, input_file):

        filename = self.get_filename(input_file)
        save_filename = self.cache_dir / f"{filename}.pkl"
        with open(save_filename, "wb") as f:
            cloudpickle.dump(document, f)

