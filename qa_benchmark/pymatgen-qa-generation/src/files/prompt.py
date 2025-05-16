question_generation_prompt = (
"""Generate five multiple-choice questions related to Pymatgen based on the following code document:

<document>
{Document}
</document>

The output must be in XML format with the following structure:

<question1>Generated question text here.</question1>
<answer_choices1>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices1>
<correct_answer1>Correct choice letter</correct_answer1>

<question2>Generated question text here.</question2>
<answer_choices2>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices2>
<correct_answer2>Correct choice letter</correct_answer2>

<question3>Generated question text here.</question3>
<answer_choices3>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices3>
<correct_answer3>Correct choice letter</correct_answer3>

<question4>Generated question text here.</question4>
<answer_choices4>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices4>
<correct_answer4>Correct choice letter</correct_answer4>

<question5>Generated question text here.</question5>
<answer_choices5>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices5>
<correct_answer5>Correct choice letter</correct_answer5>

Note:
1. Ensure the correct answer is derived from the provided content.
2. The generated question should not reference the provided document explicitly (e.g., do not mention “based on the given content”).
3. Clearly indicate that the question is related to Pymatgen and mention the module it comes from according to the document.
4. The question should be designed to be non-trivial, requiring a nuanced understanding of the function’s behavior.
5. The answer choices should be carefully designed to introduce plausible but incorrect options, making the correct answer less obvious.
6. If the given document does not contain enough content to generate five meaningful questions, generate only as many questions as possible."""
)

question_test_prompt = (
    "You are a materials scientist with expertise in Pymatgen for solving material simulation problems. "
    "Below is a multiple-choice question related to Pymatgen. Please select the correct answer based on your expertise.\n\n"
    "<question>{question}</question>\n"
    "<answer_choices>\n"
    "    <choice>{first_choice}</choice>\n"
    "    <choice>{second_choice}</choice>\n"
    "    <choice>{third_choice}</choice>\n"
    "    <choice>{fourth_choice}</choice>\n"
    "</answer_choices>\n\n"
    "Only provide your answer as a single letter (A, B, C, or D), formatted in tags as follows:\n"
    "<answer>Your answer here</answer>"
)

question_code_generation_prompt = (
"""Generate five multiple-choice questions based on the given Python code snippet.
Each question should include the code with one key function name or critical code part randomly masked as [MASK].
The task is to identify the correct replacement for [MASK] from the provided answer choices.

<code_souce_file>Code Source File: {CodeSourceFile}</code_souce_file>
<code>
{CodeSnippet}
</code>

The output must be in XML format with the following structure:

<question1>Generated question text here with a [MASK] token replacing a function or key part.</question1>
<answer_choices1>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices1>
<correct_answer1>Correct choice letter</correct_answer1>

<question2>Generated question text here with a [MASK] token replacing a function or key part.</question2>
<answer_choices2>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices2>
<correct_answer2>Correct choice letter</correct_answer2>

<question3>Generated question text here with a [MASK] token replacing a function or key part.</question3>
<answer_choices3>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices3>
<correct_answer3>Correct choice letter</correct_answer3>

<question4>Generated question text here with a [MASK] token replacing a function or key part.</question4>
<answer_choices4>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices4>
<correct_answer4>Correct choice letter</correct_answer4>

<question5>Generated question text here with a [MASK] token replacing a function or key part.</question5>
<answer_choices5>
    <choice>A. First answer choice</choice>
    <choice>B. Second answer choice</choice>
    <choice>C. Third answer choice</choice>
    <choice>D. Fourth answer choice</choice>
</answer_choices5>
<correct_answer5>Correct choice letter</correct_answer5>

Note:
1. Each question should replace a function name, method name, or critical keyword in the code with [MASK].
2. The correct answer should be derived directly from the given code snippet.
3. The generated question should give the code source file path and the code snippet context after masking the function or keyword.
4. The masked function or keyword should be significant to the logic of the code.
5. The answer choices should introduce plausible but incorrect options to challenge the reader.
6. If the given code snippet does not contain enough content to generate five meaningful questions, generate only as many questions as possible."""
)