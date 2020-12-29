class SimpleCLIUI(object):
    def __init__(self, prompt_marker=">", debug=False):
        self.debug = debug
        self.prompt_marker = prompt_marker

    def display_chunk(self, chunk):
        print(chunk)

    def display_chunk_update(self, chunk):
        pass

    def display_question(self, question):
        print("Question: {}".format(question))

    def display_search_result(self, result):
        print(result)

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

    def annotate(self, chunker, store, annotator, platform):
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
