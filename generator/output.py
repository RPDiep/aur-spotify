class Output(object):
    def print(self, message: str):
        pass

    def progress(self, progress, total):
        pass


class CmdLineOutput(Output):
    def print(self, message: str):
        print(message)

    def progress(self, progress, total):
        percentage = int(progress/total*100)
        bar_length = 50
        done = int(percentage / (100 / bar_length))
        remainder = bar_length - done

        progress_msg = "\r[{0}{1}] {2}%".format('=' * done, ' ' * remainder, percentage)
        print(progress_msg, end='')
        # Add newline when when done
        if percentage == 100:
            print()
