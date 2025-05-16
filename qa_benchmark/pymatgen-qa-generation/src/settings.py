import os
from pydantic import BaseModel, Field

CONFIG = {
    "PROMPT": "code_generation",
    "MODEL_NAME": "gemini-2.0-flash",
    "LOGGER_FILE": "question_generator_code.log",
    "OUTPUT_FILE": "files/generation_results_code.json",
}

TEST_CONFIG = {
    "MODEL_NAME": "gemini-2.0-flash",
    "MODEL_TYPE": "remote",
    "LOGGER_FILE": "question_evaluation_code_gemini-2-0-flash.log",
    "CSV_FILE_NAME": "evaluation_results_gemini-2-0-flash.csv",
    "TEST_FILE_PATH": "generation_results_doc.json",
}

class Settings(BaseModel):
    prompt_type: str = Field("question_generation", description="Type of prompt to use")
    model_name: str = Field("gemini-2.0-flash", description="Model name to use")
    logger_file: str = Field("question_generator_doc.log", description="Logger file to save logs")
    output_file: str = Field("files/generation_results_doc.json", description="Output file to save results")

    @classmethod
    def load(cls):
        return cls(
            prompt_type=CONFIG.get("PROMPT", "code_generation"),
            model_name=CONFIG.get("MODEL_NAME", "gemini-2.0-flash"),
            logger_file=CONFIG.get("LOGGER_FILE", "question_generator_code.log"),
            output_file=CONFIG.get("OUTPUT_FILE", "files/generation_results_code.json"),
        )

settings = Settings.load()


class TestSettings(BaseModel):
    model_name: str = Field("gemini-2.0-flash", description="Model name to use")
    logger_file: str = Field("question_evaluation_doc_gemini-2-0-flash.log", description="Logger file to save logs")
    csv_filename: str = Field("evaluation_results_gemini-2-0-flash.csv", description="CSV file to save results")
    test_file_path: str = Field("test.json", description="Test file path")
    model_type: str = Field("remote", description="Type of model to use")
    
    @classmethod
    def load(cls):
        return cls(
            model_name=TEST_CONFIG.get("MODEL_NAME", "gemini-2.0-flash"),
            logger_file=TEST_CONFIG.get("LOGGER_FILE", "question_evaluation_doc_gemini-2-0-flash.log"),
            csv_filename=TEST_CONFIG.get("CSV_FILE_NAME", "evaluation_results_gemini-2-0-flash.csv"),
            test_file_path=TEST_CONFIG.get("TEST_FILE_PATH", "test.json"),
            model_type=CONFIG.get("MODEL_TYPE", "remote"),
        )

test_settings = TestSettings.load()

if __name__ == "__main__":
    print(f"Prompt Type: {settings.prompt_type}")
    print(f"Model Name: {settings.model_name}")
    print(f"Logger File: {settings.logger_file}")
    print(f"Output File: {settings.output_file}")