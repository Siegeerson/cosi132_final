##TOPIC		690 -- College education
##TEAM 		Daeja, Michael G, Ben s.


##General Notes

GENERAL:
-  "be aware you can combine things in different ways" (you can weight approaches differently based on long vs short queries for example)
- may want to come up descriptions/narratives that are more representative of user queries (need to record them and put in readme)

FASTTEXT:
- asked on small context window, experiment with different ways of training fasttext (fast enough to train ourselves)
--- examples: remove low idf scoring terms from the text so we only include strings of more relevant terms (reduces noice), see if a particular part of speech is most relevant (ex. nouns), change window size
- current methods just take centroid (naive, can change)

BERT:
- break up documents into sentences/passages/paragraphs and run bert embeddings on these smaller sections and see about comparing those smaller sections