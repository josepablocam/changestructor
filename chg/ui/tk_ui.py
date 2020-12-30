import tkinter as tk
import tkinter.scrolledtext as scrolledtext


class TkUI(object):
    def __init__(self):
        self.window = tk.Tk()
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

        self.frame_qa = tk.Frame(master=self.window)
        self.frame_qa.pack(expand=True, fill=tk.BOTH)

        self.frame_question = tk.Frame(master=self.frame_qa)
        self.frame_question.pack(expand=True, fill=tk.BOTH)
        self.txt_question = tk.Text(master=self.frame_question)
        self.txt_question.pack(expand=True, fill=tk.BOTH)
        self.txt_question.insert("1.0", "Question")

        self.frame_control = tk.Frame(master=self.frame_qa)
        self.frame_control.pack(expand=True)

        self.button_submit = tk.Button(
            master=self.frame_control,
            text="Submit",
            #action=XXX,
        )
        self.button_submit.pack()

        self.frame_user = tk.Frame(master=self.frame_qa)
        self.frame_user.pack(expand=True, fill=tk.BOTH)
        self.txt_user = tk.Text(master=self.frame_user)
        self.txt_user.pack(expand=True, fill=tk.BOTH)
        self.txt_user.insert("1.0", "User code")

        self.window.mainloop()

    def display_chunk(self, chunk):
        self.txt_code.delete("1.0", tk.END)
        self.txt_code.insert("1.0", chunk)

    def prompt(self, msg, options=None):
        if options is not None:
            msg = "{} [Options={}]".format(msg, options)
        self.txt_question.delete("1.0", tk.END)
        self.txt_question.insert("1.0", msg)
        # NEED TO BLOCK
        # WAITING ON USER HIT SUBMIT


    def display_question(self, question):
        self.txt_question.delete("1.0", tk.END)
        self.txt_question.insert("1.0", question)

def annotate(self, chunker, store, annotator, platform):


    # TODO: start main event loop
    # check if chunk available, if not, exit
    # display chunk
    # display question
    # record text 


    for chunk in chunker.get_chunks():
        # show chunk to user initially
        self.display_chunk(chunk)
        # annotater gets access to chunk
        # so can produce relevant questions
        annotator.consume_chunk(chunk)

        answered = []
        while not annotator.done():
            question = annotator.ask()
            # annotator may want to update the display
            # for the chunk based on the question
            # (e.g. may want to highlight a portion of the chunk)
            chunk_update = annotator.get_chunk_update()
            self.display_chunk_update(chunk_update)

            self.display_question(question)

            answer = self.prompt("")
            # annotator can update its internal state
            # based on answer (e.g. new question based on previous answer)
            annotator.consume_answer(answer)
            answered.append((question, answer))

        # changes induced by the chunk (i.e. this diff)
        # are committed directly by `chg` (i.e. the user
        # no longer needs to interact with `git commit`)
        old_hash = platform.hash()
        # some annotators may want to generate the commit message
        # directly from the user's dialogue
        # rather than prompt user for explicit commit message
        if annotator.has_commit_message():
            # but user can always override
            generate_msg = self.prompt("Generate commit msg?", ["Y", "n"])
            if generate_msg == "Y":
                msg = annotator.get_commit_message()
            else:
                msg = self.prompt("Commit message: ")
        else:
            msg = self.prompt("Commit message: ")
            # if user writes commit message, we should take that
            # as more info for db
            answered.append(("Commit message", msg))

        # just for dev
        if not self.debug:
            chunker.commit(msg)

        new_hash = platform.hash()
        # info is only stored in the database after the commit
        # has taken place
        # TODO: if the user exits or crashes before this
        # the file system will reflect git changes, but not
        # any info in chg database, we should fix this...
        chunk_id = store.record_chunk((old_hash, chunk, new_hash))
        store.record_dialogue((chunk_id, answered))

    def ask(self, searcher, k=5):
        try:
            while True:
                user_question = self.prompt("Question: ")
                results = searcher.search(user_question, k=k)
                for r in results:
                    self.display_search_result(r)
        except (EOFError, KeyboardInterrupt):
            return


if __name__ == "__main__":
    ui = TkUI()
