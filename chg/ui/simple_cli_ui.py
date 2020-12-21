class SimpleCLIUI(object):
    def __init__(self, prompt_marker=">"):
        self.prompt_marker = prompt_marker

    def display_chunk(self, chunk):
        print(chunk)

    def display_chunk_update(self, chunk):
        pass

    def display_question(self, question):
        print("Question: {}".format(question))

    def prompt(self, msg, options=None):
        if options is not None:
            msg = "{} [Options={}]".format(msg, options)
        msg = "{} {}".format(self.prompt_marker, msg)
        res = input(msg)
        res = res.strip()
        if options is None or res in options:
            return res
        else:
            # prompt again
            self.prompt(msg, options=options)
