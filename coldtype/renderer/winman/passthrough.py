
class WinmanPassthrough():
    def __init__(self):
        self.context = None

    def set_title(self, text):
        #print("TITLE", text)
        pass
    
    def terminate(self):
        pass

    def reset(self):
        pass

    def preview_scale(self):
        return 1
    
    def turn_over(self):
        print("turning")
    
    def should_close(self):
        return False