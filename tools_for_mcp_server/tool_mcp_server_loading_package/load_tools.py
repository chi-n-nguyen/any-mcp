import os
import json

def load_all_tools(all_tool_dir_path):
    output_tool_list = []

    # dynamically load all the tools
    for filename in os.listdir(all_tool_dir_path):
        if filename.endswith(".json"):
            filepath = os.path.join(all_tool_dir_path, filename)
            with open(filepath, 'r') as f:
                tool_data = json.load(f)
                output_tool_list.append(tool_data)
    return output_tool_list