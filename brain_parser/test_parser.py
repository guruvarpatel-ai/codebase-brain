from brain_parser.universal_parser import detect_language, parse_file

# Test 1: language detection
print(detect_language("app.py"))
print(detect_language("server.js"))
print(detect_language("Main.java"))
print(detect_language("Dockerfile"))

# Test 2: parse a real file
result = parse_file("../brain_cli.py")
print(result['language'])
print(result['filepath'])