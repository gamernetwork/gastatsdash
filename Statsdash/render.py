from jinja2 import Environment, FileSystemLoader


#custom filters 
def int_comma(value):
	"""
	Converts an integer to a string containing commas every three digits
	"""
	val_str = str(value)
	split = val_str.split(".")
	val_int = split[0]
	
	try:
		val_point = "." + split[1]
	except IndexError:
		val_point = ""

	val_list = []
	for count, i in enumerate(reversed(val_int)):
		val_list.append(i)
		if (count+1) % 3 == 0:
			if len(val_int) == (count + 1):
				break
			else:
				val_list.append(",")
			
	val_list.reverse()
		
	final = "".join(val_list)
	final += val_point
	return final
	
def cut(word, part="www."):
    """
    Where word is a string
    Removes the section specified by part
    """
    split = word.split(part)
    truncated = "".join(split)
    return truncated 

def div_or_na(num, denom):
    if float(denom) > 0:
        return float(num) / float(denom)
    else:
        return "N/A"


def get_environment():
    """
    Returns Jinja2 rendering environment and creates context with custom filterss
    """
    env = Environment(loader=FileSystemLoader('Statsdash/Templates'), extensions=['jinja2.ext.loopcontrols'])
    env.filters['intcomma'] = int_comma
    env.filters['cut'] = cut
    env.globals['div_or_na'] = div_or_na
    return env
