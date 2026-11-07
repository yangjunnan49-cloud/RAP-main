"""Uninstalled standard-library interception for controlled synthetic stubs."""
from boundary_contract import artifact, stream


def text_component(text):
    data = text.encode('utf-8')
    return artifact(data, 'u1', [len(data)], 'na', 'output')


class Recorder:
    def __init__(self, binding):
        self.binding = binding
        self.events = []
        self.calls = 0

    def append(self, boundary, components):
        event = dict(id=str(len(self.events)), boundary=boundary, components=components,
                     state_coverage='unobserved')
        # Validate and freeze before accepting this event. Fail closed on recording errors.
        candidate = stream(self.binding, self.events + [event])
        self.events.append(candidate['events'][-1]['event'])

    def call(self, boundary, fn, args, capture_input, capture_output):
        self.append(boundary + ':before', capture_input())
        self.calls += 1
        try:
            result = fn(*args)
        except BaseException as error:
            self.append(boundary + ':exception', {'exception': text_component(type(error).__name__ + ':' + str(error))})
            raise
        self.append(boundary + ':after', capture_output(result))
        return result

    def sealed(self):
        return stream(self.binding, self.events)
