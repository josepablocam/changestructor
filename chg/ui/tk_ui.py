import enum
import subprocess
import sys

import tkinter as tk
import tkinter.scrolledtext as scrolledtext


def strip_ansi_colors(msg):
    proc = subprocess.Popen(
        "sed 's/\x1b\[[0-9;]*m//g'",
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    output, _ = proc.communicate(str.encode(str(msg)))
    return output.decode().strip()


class AnnotationStates(enum.Enum):
    STAGING = 0
    DIALOGUE = 1
    COMMIT = 2


class TkUI(object):
    def __init__(self, dev=False):
        self.window = tk.Tk()
        self.dev = dev

    def start(self):
        self.window.mainloop()

    def quit(self):
        self.window.destroy()
        sys.exit(0)

    def setup_annotate_ui(self):
        # annotate
        ########  #### Question #####
        #      #  # Answer | Commit #
        # code #  ###################
        #      #  #    user text   #
        ########  ###################

        self.frame_code = tk.Frame(master=self.window)
        self.frame_code.pack(fill=tk.BOTH, side=tk.LEFT)
        self.txt_code = scrolledtext.ScrolledText(master=self.frame_code)
        self.txt_code.pack(expand=True, fill=tk.BOTH)

        self.txt_code.tag_config("add", background="palegreen")
        self.txt_code.tag_config("remove", background="salmon")
        self.txt_code.configure(state=tk.DISABLED)

        self.frame_qa = tk.Frame(master=self.window)
        self.frame_qa.pack(expand=True, fill=tk.BOTH)

        self.frame_question = tk.Frame(master=self.frame_qa)
        self.frame_question.pack(expand=True, fill=tk.BOTH)
        self.txt_question = tk.Text(master=self.frame_question)
        self.txt_question.pack(expand=True, fill=tk.BOTH)
        self.txt_question.configure(state=tk.DISABLED)

        self.frame_control = tk.Frame(master=self.frame_qa)
        self.frame_control.pack(expand=True)

        self.button_submit = tk.Button(
            master=self.frame_control,
            text="Submit",
            command=self.consume_answer,
        )
        self.button_submit.pack(side=tk.LEFT)

        self.button_quit = tk.Button(
            master=self.frame_control,
            text="Quit",
            command=self.quit,
        )
        self.button_quit.pack(side=tk.LEFT)

        self.frame_user = tk.Frame(master=self.frame_qa)
        self.frame_user.pack(expand=True, fill=tk.BOTH)
        self.txt_user = tk.Text(master=self.frame_user)
        self.txt_user.pack(expand=True, fill=tk.BOTH)
        self.txt_user.insert("1.0", "Type here")
        self.window.title("chg annotate")

    def chunker_done(self):
        return len(self.chunks) == 0

    def annotate(self, chunker, store, annotator, platform):
        self.chunker = chunker
        self.chunks = self.chunker.get_chunks()
        self.store = store
        self.annotator = annotator
        self.platform = platform
        self.answered = []
        self.state = AnnotationStates.STAGING
        self.ready_to_commit = False

        self.setup_annotate_ui()
        # start out with first chunk
        self.next_chunk()
        self.start()

    def display_chunk(self, chunk):
        self.txt_code.configure(state=tk.NORMAL)
        self.txt_code.delete("1.0", tk.END)
        chunk = strip_ansi_colors(chunk)
        for ix, line in enumerate(chunk.split("\n")):
            self.txt_code.insert(tk.END, line + "\n")
            if line.startswith(("+", "-")):
                if line.startswith(("+++", "---")):
                    continue
                tag_name = "add" if line.startswith("+") else "remove"
                start_tag = "{}.0".format(ix + 1)
                end_tag = "{}.end".format(ix + 1)
                self.txt_code.tag_add(tag_name, start_tag, end_tag)
        self.txt_code.configure(state=tk.DISABLED)

    def display_question(self, question):
        self.txt_question.configure(state=tk.NORMAL)
        self.txt_question.delete("1.0", tk.END)
        self.txt_question.insert("1.0", question)
        self.txt_question.configure(state=tk.DISABLED)

    def fetch_question_answer(self):
        question = self.txt_question.get("1.0", tk.END).strip()
        answer = self.txt_user.get("1.0", tk.END).strip()
        return question, answer

    def prompt_staging(self):
        # ask if staged
        options = ["Y", "n"]
        self.display_question("Stage this chunk? {}".format(options))

    def consume_staging(self):
        # ask if staged
        options = ["Y", "n"]
        _, answer = self.fetch_question_answer()
        if answer not in options:
            self.display_question(
                "Please answer {}: Stage this chunk?".format(options)
            )
            return

        if answer == "Y":
            self.state = AnnotationStates.DIALOGUE
            self.answered = []
            if not self.dev:
                self.chunker.stage(self.chunks[0])
            self.annotator.consume_chunk(self.chunks[0])
            self.next_question()
        else:
            # remains same
            self.state = AnnotationStates.STAGING
            # but prompt next chunk
            self.chunks.pop(0)
            self.next_chunk()

    def next_chunk(self):
        if self.chunker_done():
            self.quit()

        chunk = self.chunks[0]
        self.display_chunk(chunk)
        self.prompt_staging()
        self.state = AnnotationStates.STAGING

    def clear_user_text(self):
        self.txt_user.delete("1.0", tk.END)

    def next_question(self):
        if not self.annotator.done():
            question = self.annotator.ask()
            self.display_question(question)
        else:
            # done with qa and should move to commit
            self.display_question("Commit message:")
            self.state = AnnotationStates.COMMIT

    def consume_answer(self, get_next_question=True):
        if self.state == AnnotationStates.STAGING:
            self.consume_staging()
        elif self.state == AnnotationStates.DIALOGUE:
            question, answer = self.fetch_question_answer()
            self.annotator.consume_answer(answer)
            self.answered.append((question, answer))
            self.next_question()
        elif self.state == AnnotationStates.COMMIT:
            self.commit_chunk()
        else:
            raise Exception("Unhandled state: {}".format(self.state))
        self.clear_user_text()

    def commit_chunk(self):
        _, commit_msg = self.fetch_question_answer()
        old_hash = self.platform.hash()

        chunk = self.chunks.pop(0)
        if not self.dev:
            self.chunker.commit(chunk, commit_msg)
            new_hash = self.platform.hash()
            chunk = self.txt_code.get("1.0", tk.END)
            chunk_id = self.store.record_chunk((old_hash, chunk, new_hash))
            self.store.record_dialogue((chunk_id, self.answered))

        self.state = AnnotationStates.STAGING
        self.next_chunk()

    def setup_ask_ui(self):
        # ask
        ##############
        ### Search: ##
        ### Results ##
        ##############

        self.frame_qa = tk.Frame(master=self.window)
        self.frame_qa.pack(expand=True, fill=tk.BOTH)

        self.txt_question = tk.Entry(master=self.frame_qa)
        self.txt_question.pack(side=tk.LEFT)

        self.button_submit = tk.Button(
            master=self.frame_qa,
            text="Search",
            command=self.run_query,
        )
        self.button_submit.pack(side=tk.LEFT)

        self.button_quit = tk.Button(
            master=self.frame_qa,
            text="Quit",
            command=self.quit,
        )
        self.button_quit.pack(side=tk.LEFT)

        self.frame_results = tk.Frame(master=self.window)
        self.frame_results.pack(fill=tk.BOTH)

        self.txt_results = scrolledtext.ScrolledText(master=self.frame_results)
        self.txt_results.pack(expand=True, fill=tk.BOTH)
        self.txt_results.configure(state=tk.DISABLED)

        self.window.title("chg ask")

    def ask(self, searcher, k=5):
        self.searcher = searcher
        self.setup_ask_ui()
        self.window.mainloop()

    def run_query(self):
        question = self.txt_question.get().strip()
        if len(question) == 0:
            return
        results = self.searcher.search(question, k=5)
        self.display_results(results)

    def display_results(self, results):
        self.txt_results.configure(state=tk.NORMAL)
        for r in results:
            r_str = str(r)
            self.txt_results.insert(tk.END, r_str + "\n")
        self.txt_results.configure(state=tk.DISABLED)


if __name__ == "__main__":
    ui = TkUI()
