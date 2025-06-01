 # mindmap_generator.py
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import graphviz 
import base64   
import io       

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MINDMAP_MODEL_NAME = "models/gemini-1.5-flash-latest"

def generate_mind_map_data(text, max_new_tokens=1500):
    """
    Generates mind map data (nodes and links) using Google Gemini API,
    then visualizes it as a PNG image.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set for mind map generation.")
        return "data:image/svg+xml;base64," + base64.b64encode(b"<svg width='100' height='50'><text x='0' y='30' fill='red'>API Key Missing</text></svg>").decode('utf-8')

    model = genai.GenerativeModel(MINDMAP_MODEL_NAME)

    prompt = f"""
    Based on the following document content, extract key concepts/entities and the relationships between them.
    Focus on the most important information and connections.
    Format your response *strictly* as a JSON object with two top-level keys: "nodes" and "links".

    Each node in the "nodes" array should be an object with an "id" (the concept name) and an optional "type" (e.g., "Concept", "Category", "Detail").
    Each link in the "links" array should be an object with a "source" (id of the starting node), a "target" (id of the ending node), and a "relation" (a brief description of the relationship).

    Example JSON structure:
    {{
      "nodes": [
        {{"id": "Artificial Intelligence", "type": "Concept"}},
        {{"id": "Machine Learning", "type": "Concept"}},
        {{"id": "Neural Networks", "type": "Detail"}}
      ],
      "links": [
        {{"source": "Artificial Intelligence", "target": "Machine Learning", "relation": "includes"}},
        {{"source": "Machine Learning", "target": "Neural Networks", "relation": "uses"}}
      ]
    }}

    Document Content:
    {text}

    JSON Output:
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=max_new_tokens,
                response_mime_type="application/json"
            )
        )
        
        generated_text = response.text.strip()
        
        try:
            mind_map_json = json.loads(generated_text)
            if "nodes" not in mind_map_json or "links" not in mind_map_json:
                raise ValueError("Missing 'nodes' or 'links' in generated JSON.")
        except json.JSONDecodeError as e:
            print(f"Gemini API returned invalid JSON: {generated_text[:500]}... Error: {e}")
        
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                try:
                    extracted_json_str = generated_text[start_idx : end_idx + 1]
                    mind_map_json = json.loads(extracted_json_str)
                    if "nodes" not in mind_map_json or "links" not in mind_map_json:
                        raise ValueError("Missing 'nodes' or 'links' in extracted JSON.")
                except Exception as ex:
                    print(f"Failed to extract JSON from malformed response: {ex}")
                    return "data:image/svg+xml;base64," + base64.b64encode(b"<svg width='200' height='50'><text x='0' y='30' fill='red'>JSON Extraction Failed</text></svg>").decode('utf-8')
            else:
                return "data:image/svg+xml;base64," + base64.b64encode(b"<svg width='200' height='50'><text x='0' y='30' fill='red'>Invalid JSON Response</text></svg>").decode('utf-8')
        
        # Graphviz Visualization
        dot = graphviz.Digraph(
            comment='Mind Map',
            format='png', # Output format
            graph_attr={
                'rankdir': 'LR', # Layout direction: Left to Right 
                'bgcolor': '#f7f7f7', 
                'overlap': 'false', 
                'splines': 'true', # Draw curvy lines
                'fontsize': '12',
                'fontname': 'Roboto',
                'margin': '0.5'
            },
            node_attr={
                'shape': 'box', # Box shape for nodes
                'style': 'filled',
                'fillcolor': '#aed6f1', # Light blue nodes
                'color': '#3498db', # Darker blue border
                'fontname': 'Montserrat',
                'fontsize': '14',
                'penwidth': '2.0',
                'margin': '0.2,0.1' # Padding inside node
            },
            edge_attr={
                'color': '#7f8c8d', # Gray edges
                'fontname': 'Roboto',
                'fontsize': '10',
                'fontcolor': '#555555'
            }
        )

        # Adding nodes
        for node_data in mind_map_json.get("nodes", []):
            node_id = node_data.get("id")
            node_type = node_data.get("type", "Concept") # Default type
            
            # Customize node colors based on type
            if node_type == "Concept":
                fill_color = '#aed6f1' 
            elif node_type == "Person":
                fill_color = '#d4aed1' 
            elif node_type == "Organization":
                fill_color = '#aed1c9' 
            elif node_type == "Event":
                fill_color = '#f1c40f' 
            else:
                fill_color = '#f1d4b1' 

            if node_id: 
                dot.node(str(node_id), label=str(node_id), fillcolor=fill_color)

        # Adding edges
        for link_data in mind_map_json.get("links", []):
            source_id = link_data.get("source")
            target_id = link_data.get("target")
            relation = link_data.get("relation", "")

            if source_id and target_id: 
                dot.edge(str(source_id), str(target_id), label=str(relation))

        # Rendering the graph to bytes
        img_bytes = dot.pipe(format='png')

        base64_img = base64.b64encode(img_bytes).decode('utf-8')

        return f"data:image/png;base64,{base64_img}"
        
    except Exception as e:
        print(f"Error during Gemini API mind map data generation or Graphviz rendering: {e}")
        return "data:image/svg+xml;base64," + base64.b64encode(b"<svg width='200' height='50'><text x='0' y='30' fill='red'>Generation Error</text></svg>").decode('utf-8')

# Local Testing the mind map generation function
if __name__ == '__main__':
    sample_text = """
    The Internet of Things (IoT) is a revolutionary paradigm that connects everyday objects to the internet, enabling them to send and receive data. Key components of IoT include sensors, actuators, and network connectivity. Data collected by IoT devices is often processed in cloud computing environments. Companies like Amazon (AWS IoT) and Microsoft (Azure IoT) offer platforms for managing IoT devices. Security is a major concern in IoT deployments.
    """
    print("Run Flask app and try in browser.")