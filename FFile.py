def read_and_print_txt(file_path):
    """Reads a .txt file and prints its content to the console."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            print(content)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except PermissionError:
        print(f"Error: You do not have permission to read '{file_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage:
read_and_print_txt('wordlist.txt')