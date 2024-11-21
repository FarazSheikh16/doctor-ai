from src.wiki import WikipediaPageProcessor

page_title = "Basal-cell carcinoma"
processor = WikipediaPageProcessor(page_title)
processor.fetch_wikitext()
processor.clean_wikitext()
processor.create_chunks()
processor.print_chunks()
processor.save_chunks(f"{page_title.replace(' ', '_')}_chunks.json")
