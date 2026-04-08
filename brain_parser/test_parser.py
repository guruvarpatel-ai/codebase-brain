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
print(result['functions'])
print(result['classes'])
print(result["imports"])

result3 = parse_file("../test_js.js")
print(result3['language'])
print(result3['filepath'])
print(result3['functions'])
print(result3["classes"])
print(result3["imports"])
result4 = parse_file("../test.java")
print(result4['language'])
print(result4['functions'])
print(result4['classes'])
print(result4['imports'])
