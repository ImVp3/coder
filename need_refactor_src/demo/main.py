import gradio as gr
from . import utils

MODEL_CHOICES = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]
class ChatUI :
    def __init__(self, vector_store, graph) :
        self.vector_store = vector_store
        self.graph = graph
        
    def create_ui (self):
        with gr.Blocks() as app:
            gr.Markdown("# Code Assistant")
            chat_tab = self._create_chat_tab()
            documents_tab = self._create_documents_tab()
        return app
    def _create_chat_tab (self):
        with gr.Tab(label="Chat") as chat_tab:
            gr.Markdown("## Chat")
            with gr.Sidebar(label= "Code Generation Settings", position="right") as sidebar:
                model_selection = gr.Dropdown(
                    choices= MODEL_CHOICES,
                    value= MODEL_CHOICES[0],
                    label= "Model",
                    interactive= True
                )
                temperature = gr.Slider(
                    minimum= 0.0,
                    maximum= 1.0,
                    step= 0.1,
                    value= 0.0,
                    label= "Temperature",
                )
                max_iterations = gr.Slider(
                    minimum= 1,
                    maximum= 10,
                    step= 1,
                    value= 3,
                    label= "Max Iterations",
                    interactive= True
                )
                reflect = gr.Checkbox(
                    value= True,
                    label= "Reflect",
                )
                framework = gr.Textbox(
                    placeholder= "Enter the framework",
                    label= "Framework",
                )
                save_btn = gr.Button(
                    "Save",
                    interactive= True,
                )
                update_status = gr.Textbox(
                    container= False,
                    interactive= False,
                    label= "Status",
                )
                save_btn.click(
                    fn= self.graph.change_parameters,
                    inputs= [model_selection, temperature,max_iterations, reflect, framework],
                    outputs= update_status
                )
            chat_interface = gr.ChatInterface(
                fn = self.chat_fn,
                type = "messages",
            )
    def chat_fn (self,message, history):
        response = self.graph.invoke(message)
        return {
            "role": "assistant",
            "content": response["messages"][-1].content
        }
    def _create_documents_tab (self):
        with gr.Tab(label="Documents") as document_tab:
            with gr.Row():
                with gr.Column(scale= 1):
                    with gr.Tabs():
                        with gr.Tab("Upload by Links"):
                            url_input = gr.Textbox(
                                label="URL", 
                                placeholder="https://example.com/docs/"
                            )
                            max_depth = gr.Slider(
                                minimum= 0,
                                maximum= 10,
                                step=1,
                                label= "Max Depth",
                                interactive= True,
                            )
                            url_btn = gr.Button ("Save")
                        with gr.Tab("Upload by Files"):
                            file_uploader = gr.Files ( 
                                                    file_types= [".pdf", ".txt", ".md"],
                                                    allow_reordering=True
                                                    )
                            file_btn = gr.Button("Upload")
                        status = gr.Textbox(
                            label= "Status",
                            placeholder= "Status",
                            container= False,
                            interactive= False,
                            
                        )
                    delete_docs = gr.Textbox(
                        placeholder="Source to delete",
                        interactive= True,
                        show_label= False,
                        submit_btn= "Delete"
                    )
                with gr.Column(scale= 3):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("## List of Sources")
                            source_list = gr.List(
                                label= "Source List",
                                interactive= False,
                                show_row_numbers=True,
                                show_search="filter",
                                datatype="html",
                                value= self.vector_store.list_source()
                            )
                url_btn.click( 
                    fn= lambda url_input, max_depth: utils.handle_url_btn(url_input, max_depth, self.vector_store) ,
                    inputs = [url_input, max_depth],
                    outputs= [status,source_list]
                )
                file_btn.click(
                    fn= lambda file_uploader: utils.handle_file_btn(file_uploader, self.vector_store),
                    inputs= [file_uploader],
                    outputs= [status,source_list]
                )
                delete_docs.submit(
                    fn= lambda source: utils.handle_delete_source(source, self.vector_store),
                    inputs= [delete_docs],
                    outputs= [status, source_list]
                )
        return document_tab 