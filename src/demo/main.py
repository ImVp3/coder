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
            documents_tab = self._create_documents_tab()
            chat_tab = self._create_chat_tab()
        return app
    def _create_chat_tab (self):
        with gr.Tab(label="Chat") as chat_tab:
            gr.Markdown("## Chat")
            chatbot = gr.Chatbot()
            msg = gr.Textbox(label="Input")
            clear = gr.Button("Clear")
            status = gr.Textbox(label="Current Flow", interactive=False)
            
            with gr.Sidebar(label= "Settings", position="right") as sidebar:
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

            def user(user_message, history):
                return "", history + [[user_message, None]]

            def bot(history):
                user_message = history[-1][0]
                history[-1][1] = ""
                
                # Stream the response
                for state in self.graph.stream(user_message):
                    if "flow" in state:
                        # Update flow status
                        flow_str = " -> ".join(state["flow"])
                        yield history, flow_str
                    
                    if "generation" in state and state["generation"]:
                        # Get the last message
                        last_message = utils.parse_code_generation(state["generation"][-1])
                        history[-1][1] = last_message
                        yield history, flow_str
                yield history, flow_str
            msg.submit(user, [msg, chatbot], [msg, chatbot]).then(
                bot, chatbot, [chatbot, status]
            )
            clear.click(lambda: None, None, chatbot, queue=False)
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