
from langchain_text_splitters import CharacterTextSplitter
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Text
from unstructured.cleaners.core import replace_unicode_quotes
from unstructured.cleaners.core import clean
from unstructured.cleaners.core import clean_non_ascii_chars
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama


# Generate summaries of text elements
def generate_text_summaries(texts, tables, summarize_texts=False):
    """
    Summarize text elements
    texts: List of str
    tables: List of str
    summarize_texts: Bool to summarize texts
    """

    # Prompt
    prompt_text = """You are an assistant tasked with summarizing tables and text for retrieval. \
    These summaries will be embedded and used to retrieve the raw text or table elements. \
    Give a concise summary of the table or text that is well optimized for retrieval. Table or text: {element} """
    prompt = ChatPromptTemplate.from_template(prompt_text)

    # Text summary chain
    model = ChatOllama(model="llama3")
    summarize_chain = {"element": lambda x: x} | prompt | model | StrOutputParser()

    # Initialize empty summaries
    text_summaries = []
    table_summaries = []

    # Apply to text if texts are provided and summarization is requested
    if texts and summarize_texts:
        print("text summarize")
        text_summaries = summarize_chain.batch(texts, {"max_concurrency": 5})
    elif texts:
        text_summaries = texts

    # Apply to tables if tables are provided
    if tables:
        print("tables summarize")
        table_summaries = summarize_chain.batch(tables, {"max_concurrency": 5})
        print(table_summaries)

    return text_summaries, table_summaries

# Extract elements from PDF
def extract_pdf_elements(path, fname):
    """
    Extract images, tables, and chunk text from a PDF file.
    path: File path, which is used to dump images (.jpg)
    fname: File name
    """
    return partition_pdf(
        filename=path + fname,
        extract_images_in_pdf=True,
        infer_table_structure=True,
        chunking_strategy="by_title",
        max_characters=4000,
        new_after_n_chars=3800,
        combine_text_under_n_chars=2000,
        image_output_dir_path="./RAG2/figures/",
    )


# Categorize elements by type
def categorize_elements(raw_pdf_elements):
    """
    Categorize extracted elements from a PDF into tables and texts.
    raw_pdf_elements: List of unstructured.documents.elements
    """
    tables = []
    texts = []
    for element in raw_pdf_elements:
        if "unstructured.documents.elements.Table" in str(type(element)):
            tables.append(str(element))
        elif "unstructured.documents.elements.CompositeElement" in str(type(element)):
            texts.append(str(element))
    return texts, tables

def clean_text(texts):
    texts = [replace_unicode_quotes(text) for text in texts]
    texts = [remove_links(text) for text in texts]
    texts = [clean(text, bullets=True, lowercase=True,extra_whitespace=True, dashes=True) for text in texts]
    texts = [clean_non_ascii_chars(text) for text in texts]
    return texts


def extract(fpath,fname):
    # File path
    # fpath = "RAG2/"
    # fname = "test.pdf"
    print("Start partition")
    # Get elements
    raw_pdf_elements = extract_pdf_elements(fpath, fname)
    print("partition done!")
    # Get text, tables
    texts, tables = categorize_elements(raw_pdf_elements)

    # Optional: Enforce a specific token size for texts
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=4000, chunk_overlap=0
    )
    joined_texts = " ".join(texts)
    texts_4k_token = text_splitter.split_text(joined_texts)
    # Get text, table summaries
    text_summaries, table_summaries = generate_text_summaries(
        texts_4k_token, tables, summarize_texts=False
    )
    print("text and table summaries finished")
    return texts,tables,text_summaries, table_summaries