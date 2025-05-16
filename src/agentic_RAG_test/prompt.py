

query_generation_prompt_str = (
    "You are a helpful assistant that generates multiple search queries based on a "
    "single input query. Generate {num_queries} search queries, one on each line, "
    "related to the following input query:\n"
    "Query: {query}\n"
    "Queries:\n"
)

# Relevance Ranking Prompt
relevance_ranking_instruction = (
    "You are an expert relevance ranker. Given a list of documents and a query, your job is to determine how relevant each document is for answering the query. "
    "Your output must be a valid JSON object with the key 'documents', strictly following this format:\n\n"
    "{\n"
    "  \"documents\": [\n"
    "    {\"content\": \"Document 1 text...\", \"relevance_score\": 85.5},\n"
    "    {\"content\": \"Document 2 text...\", \"relevance_score\": 72.0},\n"
    "    {\"content\": \"Document 3 text...\", \"relevance_score\": 45.0}\n"
    "  ]\n"
    "}\n\n"
    "Do not include any additional text before or after the JSON output. The JSON output must be directly parsable using `json.loads`."
)

relevance_ranking_guideline = "Query: {query}\n\nDocs: {docs}"

rag_prompt_str = (
    "You are a helpful assistant in the Pymatgen repository Q&A. Users will ask questions about something contained in the Pymatgen repository. "
    "You will be shown the user's question and the relevant information from the repository. Answer the user's question only with the given information.\n\n"
    "If a result can be directly obtained using simple Python operations such as '==', prefer Python's built-in capabilities over methods that do not exist in Pymatgen.\n\n"
    "Question: {query}.\n\n"
    "Information: {information}"
)

rag_ar_prompt_str = (
    "You are a helpful Repository-Level Software Q&A assistant. Your task is to answer users' questions based on the given information about the Pymatgen repository, "
    "including related code and documents.\n\n"
    "Currently, you're in the Pymatgen project. The user's question is:\n"
    "{query}\n\n"
    "Now, you are given related code and documents as follows:\n\n"
    "-------------------Code-------------------\n"
    "Some most likely related code snippets recalled by the retriever are:\n"
    "{related_code}\n\n"
    "-------------------Document-------------------\n"
    "Some most relevant documents recalled by the retriever are:\n"
    "{embedding_recall}\n\n"
    "Please note:   \n"
    "1. All the provided recall results are related to the current project Pymatgen. Please filter useful information according to the user's question and provide the most relevant function as the answer.\n"
    "2. If a result can be directly obtained using simple Python operations such as '==', prefer Python's built-in capabilities over methods that do not exist in Pymatgen.\n\n"
    "3. Your output must be a valid JSON object with the keys 'function_name' and 'function', strictly following this format:\n\n"
    "{{\n"
    "  \"function_name\": \"calculate_sum\",\n"
    "  \"function\": \"def calculate_sum(a, b):\\n    return a + b\"\n"
    "}}\n\n"
    "Do not include any additional text before or after the JSON output. The JSON output must be directly parsable using `json.loads`."
)