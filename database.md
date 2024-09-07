SELECT 
    table_name, 
    column_name, 
    data_type 
FROM 
    information_schema.columns 
WHERE 
    table_name = 'inputs';

table_name	column_name	data_type
inputs	id	integer
inputs	document_name	text
inputs	document_url	text
inputs	document_contents	text
inputs	document_summary	text
inputs	document_type	text