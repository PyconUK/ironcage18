from django import template

register = template.Library()


@register.filter()
def index(value, index):
    return value[index]

@register.simple_tag
def get_session_title(sessions, room, time):
    session = sessions.get(time, {}).get(room, None)
    if session:
        return session['title']
    return ''


@register.simple_tag
def get_session_speaker(sessions, room, time):
    session = sessions.get(time, {}).get(room, None)
    if session:
        return session['name']
    return ''


@register.simple_tag
def get_session_rows(sessions, room, time):
    session = sessions.get(room, {}).get(time, None)
    if session and session['rows'] > 1:
        return 'rowspan=%s' % session['rows']
    return ''


from django.template import Library, Node, TemplateSyntaxError

# register = Library()

@register.tag
def ifsession(parser, token):
    # Separating the tag name from the "test" parameter.

    try:
        tag, sessions_name, room_name, time_name = token.split_contents()
    except (ValueError, TypeError):
        raise TemplateSyntaxError(
            "'%s' tag takes four parameters" % tag)

    default_states = ['ifsession', 'long_session', 'no_session']
    end_tag = 'endifsession'

    # Place to store the states and their values
    states = {}

    # Let's iterate over our context and find our tokens
    while token.contents != end_tag:
        current = token.contents
        states[current.split()[0]] = parser.parse(default_states + [end_tag])
        token = parser.next_token()

    sessions_var = parser.compile_filter(sessions_name)
    room_var = parser.compile_filter(room_name)
    time_var = parser.compile_filter(time_name)
    return IfSessionNode(states, sessions_var, room_var, time_var)


class IfSessionNode(Node):
    def __init__(self, states, sessions_var, room_var, time_var):
        self.states = states
        self.sessions_var = sessions_var
        self.room_var = room_var
        self.time_var = time_var

    def render(self, context):
        # Resolving variables passed by the user
        sessions = self.sessions_var.resolve(context, True)
        room = self.room_var.resolve(context, True)
        time = self.time_var.resolve(context, True)

        # Rendering the right state. You can add a function call, use a
        # library or whatever here to decide if the value is true or false.
        session = sessions.get(time) and sessions[time].get(room)
        if session is None:
            return self.states['no_session'].render(context)
        elif session.get('long_session', False):
            return self.states['long_session'].render(context)
        else:
            return self.states['ifsession'].render(context)

