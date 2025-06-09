import os

# Danh sách các thư mục cần tạo
folders = [
    "src/config",
    "src/api/routes",
    "src/api/middleware",
    "src/api/schemas",
    "src/core/domain",
    "src/core/application/services",
    "src/core/application/use_cases",
    "src/core/infrastructure/database",
    "src/core/infrastructure/vectorstore",
    "src/core/infrastructure/llm",
    "src/core/interfaces",
    "src/core/agents/nodes",
    "src/utils",
    "src/di",
    "src/demo",
    "src/tests/unit",
    "src/tests/integration",
    "src/tests/e2e",
]

# Tạo từng thư mục
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    init_path = os.path.join(folder, '__init__.py')
    with open(init_path, 'w') as f:
        pass  # Tạo __init__.py trống

# Tạo file gốc ngoài thư mục
with open("src/app.py", "w") as f:
    f.write("# Entry point\n")

print("✅ Tạo cấu trúc thư mục thành công.")
