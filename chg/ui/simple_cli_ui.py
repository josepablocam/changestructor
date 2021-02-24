class SimpleCLIUI(object):
    def __init__(self, prompt_marker=">", dev=False):
        self.dev = dev
        self.prompt_marker = prompt_marker

    def display_chunk(self, chunk):
        print(chunk)

    def display_question(self, question):
        print("Question: {}".format(question))

    def display_search_result(self, result):
        print(result)

    def prompt(self, msg, options=None):
        formatted_msg = "{} {} ".format(self.prompt_marker, msg)
        if options is not None:
            formatted_msg += "[Options={}] ".format(options)
        res = input(formatted_msg)
        res = res.strip()
        if options is None or res in options:
            return res
        else:
            # prompt again
            self.prompt(msg, options=options)

    def annotate_helper(self, chunker, store, annotator, platform):
        for chunk in chunker.get_chunks():
            # show chunk to user initially
            self.display_chunk(chunk)

            answer = self.prompt("Stage?", ["Y", "n"])
            if answer == "n":
                # skip
                continue

            if not self.dev:
                chunker.stage(chunk)

            # annotater gets access to chunk
            # so can produce relevant questions
            annotator.consume_chunk(chunk)

            answered = []
            while not annotator.done():
                question = annotator.ask()
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
            if not self.dev:
                chunker.commit(msg, chunk)

                new_hash = platform.hash()
                # info is only stored in the database after the commit
                # has taken place
                # TODO: if the user exits or crashes before this
                # the file system will reflect git changes, but not
                # any info in chg database, we should fix this...
                chunk_id = store.record_chunk((old_hash, chunk, new_hash))
                store.record_dialogue((chunk_id, answered))

    def annotate(self, chunker, store, annotator, platform):
        try:
            self.annotate_helper(chunker, store, annotator, platform)
        except (EOFError, KeyboardInterrupt):
            return

    def ask(self, searcher, k=5):
        try:
            while True:
                user_question = self.prompt("Question: ")
                results = searcher.search(user_question, k=k)
                for r in results:
                    self.display_search_result(r)
        except (EOFError, KeyboardInterrupt):
            return
