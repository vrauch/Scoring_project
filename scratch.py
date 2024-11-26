
from db_config import execute_query



# Test execute_query to ensure it's working as expected
test_query = "SELECT * FROM e2caf.Domain LIMIT 5;"
test_results = execute_query(test_query)
print(test_results)
