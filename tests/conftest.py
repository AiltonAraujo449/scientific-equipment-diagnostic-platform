
import os

# Desativa o banco nos testes comuns, mas permite testes de integração
# quando SEDP_RUN_DB_TESTS=1.
if os.getenv("SEDP_RUN_DB_TESTS") != "1":
    os.environ["SEDP_DB_ENABLED"] = "false"