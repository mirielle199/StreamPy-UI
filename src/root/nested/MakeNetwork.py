from Stream import Stream
from Stream import _no_value, _multivalue
from Agent import Agent
from OperatorsTest import stream_agent

from pprint import pprint
from example import *
from components_test import *
import re
from array import array
#from root.nested.Stream_Learn import stream_learn


def make_network(stream_names_tuple, agent_descriptor_dict):
    """ This function makes a network of agents given the names
    of the streams in the network and a description of the
    agents in the network.

    Parameters
    ----------
    stream_names_tuple: tuple of lists
        A tuple consisting of names of streams in the network.
        Each stream in the network must have a unique name.
    agent_descriptor_dict: dict of tuples
        The key is an agent name
        The value is a tuple:
           in_list, out_list, f, f_type, f_args, state
           where:
             in_list: list of input stream names
             out_list: list of output stream names
             f: function associated with the agent
             f_type: 'element', 'list', 'window', etc
             f_args: tuple of arguments for functions f
             state: the state associated with this agent.

    Local Variables
    ---------------
    stream_dict: dict
          key: stream name
          value: Stream
    agent_dict: dict
          key: agent name
          value: agent with the specified description:
                 in_list, out_list, f, f_type, f_args, state,
                 call_streams=[timer_stream]
                 where one timer stream is associated with
                 each agent.
    agent_timer_dict: dict
          key: agent_name
          value: Stream
          The value is the timer stream associated with the
          agent. When the timer stream has a message, the
          agent is made to execute a step.

    """
    # Create streams and insert streams into stream_dict.
    stream_dict = dict()
    for stream_name in stream_names_tuple:
        stream_dict[stream_name] = Stream(stream_name)

    agent_dict = dict()
    agent_timer_dict = dict()

    # Create agents with the specified description
    # and put the agents into agent_dict.
    for agent_name in agent_descriptor_dict.keys():
        print 'agent_name:', agent_name
        in_list, out_list, f, f_type, f_args, state, call_streams = \
          agent_descriptor_dict[agent_name]
        
        ## # Only for debugging
        ## print 'in_list', in_list
        ## print 'out_list', out_list
        ## print 'f', f
        ## print 'f_args', f_args
        ## print 'f_type', f_type
        ## print 'state', state

        # Replace a list consisting of a single input stream
        # by the stream itself.
        if len(in_list) == 1:
            single_input_stream_name = in_list[0]
            #print 'stream dict is:'
            #pprint(stream_dict)
            inputs = stream_dict[single_input_stream_name]
        else:
            inputs = list()
            for input_stream_name in in_list:
                inputs.append(stream_dict[input_stream_name])

        # Replace a list consisting of a single output stream
        # by the stream itself.
        if len(out_list) == 1:
            single_output_stream_name = out_list[0]
            outputs = stream_dict[single_output_stream_name]
        else:
            outputs = list()
            for output_stream_name in out_list:
                outputs.append(stream_dict[output_stream_name])
        
        # Create timer streams and insert them into agent_timer_dict 
        agent_timer_dict[agent_name] = Stream(
            agent_name + ':timer')
        #print agent_timer_dict
        
        ## Create agents and insert them into agent_dict
        agent_dict[agent_name] = stream_agent(
            inputs, outputs, f_type, f, f_args, state,
            call_streams=[agent_timer_dict[agent_name]])

        # Set the name for this agent.
        agent_dict[agent_name].name = agent_name

    return (stream_dict, agent_dict, agent_timer_dict)

## Convert string to the correct object type (int, float, string)
def cast(s):
    try:
        int(s)
        return float(s)
    except ValueError:
        try:
            float(s)
            return int(s)
        except ValueError:
            return str(s)

## This goes from Flowhub's JSON to our JSON    
# key: agent name
# value: list of input streams, list of output streams, function, function type,
#        tuple of arguments, state
#Eg. 'generate_random': [
#            [], ['random_stream'], rand, 'element', (100,), None],
def make_agent_descriptor_dict(instance_dict, comp_list):
    dic = {}
    json_dic = {}
    # TODO: find a better way to do this
    # Currently a hard-coded string-to-function_object dict 
    f_dict = {'generate_of_random_integers': generate_of_random_integers, 
              'split_into_even_odd': split_into_even_odd, 
              'print_value': print_value, 
              'multiply_elements': multiply_elements,
              'split': split,
              #'stream_learn': stream_learn,
              #'get_data': get_data
              }

    for stream in instance_dict:
        s_name, s_id = clean_id(stream.split('/')[1])
        s_name = new_name(comp_list, s_name, s_id)
        dic[s_name] = [0, 0, 0, 0, 0, 0]
        json_dic[s_name] = []
        
        state = None
        func = str()
        type = 'element'
        param = ()
        
        # (Default function name: component name with "_stream" removed)
        # Get rid of the instance id (ie. 0, 1, 2...) to get function name
        func = s_name.replace('_stream', '')
        m = re.search(r'\d+$', func)
        if m is not None:
            func = func.replace(m.group(), '')
        
        input = []
        for i in instance_dict[stream]['in']:
            if '=' not in i:
                src_name_id, src_port = clean_id(i.split('/')[1])
                src_name, src_id = clean_id(src_name_id)
                
                src_name = new_name(comp_list, src_name, src_id)
                input.append(src_name + '_PORT_' + src_port)
                
            else:
                data_name = i.split('=')[0]
                data_val = cast(i.split('=')[1])
                if data_name == 'state':
                    state = data_val
                elif data_name == 'type':
                    type = data_val
                elif data_name == 'func':
                    func = data_val
                else:
                    param = param + (data_val,)
                    
        output = []
        for i in instance_dict[stream]['out']:
            src_name_id, src_port = clean_id(i.split('/')[1])
            src_name, src_id = clean_id(src_name_id)

            src_name = new_name(comp_list, src_name, src_id)

            output.append(src_name + '_PORT_' + src_port)
        
        if param == ():
            param = None
        

        dic[s_name][0] = input
        dic[s_name][1] = output
        dic[s_name][2] = func
        dic[s_name][3] = type
        dic[s_name][4] = param
        dic[s_name][5] = state
                
        json_dic[s_name] = [input, output, func, type, param, state]
    
    json_dic = json.dumps(json_dic, sort_keys=True, 
                              indent=4, separators=(',', ': '))    

    return json_dic



# Make stream_names_tuple from Flowhub's JSON
# Returns the JSON str equivalent of stream_names_tuple
def make_stream_names_tuple(instance_dict, comp_list):
    stream_names_tuple = ()
    for comp in instance_dict:
        for i in instance_dict[comp]['in']:

            # For input streams (not parameters)
            if '=' not in i:
                #Replace random id with 0, 1, 2...
                src_name_id, src_port = clean_id(i.split('/')[1])
                src_name, src_id = clean_id(src_name_id)
    
                src_name = new_name(comp_list, src_name, src_id)
    
                s = src_name + '_PORT_' + src_port
                if s not in stream_names_tuple:
                    stream_names_tuple = stream_names_tuple + (s,)

        for i in instance_dict[comp]['out']:

            #Replace random id with 0, 1, 2...
            src_name_id, src_port = clean_id(i.split('/')[1])
            src_name, src_id = clean_id(src_name_id)

            src_name = new_name(comp_list, src_name, src_id)

            s = src_name + '_PORT_' + src_port

            if s not in stream_names_tuple:
                stream_names_tuple = stream_names_tuple + (s,)

    stream_names_tuple_json = json.dumps(stream_names_tuple, sort_keys=True, 
                              indent=4, separators=(',', ': '))
    return stream_names_tuple_json
'''
## Generate my special JSON file
def make_my_JSON(instance_dict, comp_list):

    stream_names_tuple = make_stream_names_tuple(instance_dict, comp_list)
    agent_descriptor_dict = make_agent_descriptor_dict(instance_dict, comp_list)
    
    output_file_name = 'agent_descriptor.json'
    f = open(output_file_name, 'w')
    f.write('{\n')
    f.write('\"agent_descriptor_dict\":\n')
    f.write(agent_descriptor_dict)
    f.write(',\n')
    f.write('\"stream_names_tuple\":\n')
    f.write(stream_names_tuple)
    f.write('\n}')
    f.close()
    return output_file_name
'''
## Grab JSON in my special format and turn into dict to execute
def JSON_to_descriptor_dict_and_stream_names(my_json_file_name):
    ## Import json file
    with open(my_json_file_name) as data_file:    
        json_data = json.load(data_file)
    
    ## Convert str to objects
    agent_descriptor_dict = json_data['agent_descriptor_dict']
    copy = json_data['agent_descriptor_dict']
    
    # TODO: find a better way to do this
    # Currently a hard-coded string-to-function_object dict 
    f_dict = {'generate_of_random_integers': generate_of_random_integers, 
              'split_into_even_odd': split_into_even_odd, 
              'print_value': print_value, 
              'multiply_elements': multiply_elements,
              'split': split,
              #'stream_learn': stream_learn,
              #'get_data': get_data
              }
    
    for agent in agent_descriptor_dict:
        
        ## func: str to function object
        func_str = agent_descriptor_dict[agent][2] 
        agent_descriptor_dict[agent][2] = f_dict[func_str]
        
        ## type: from unicode to str
        agent_descriptor_dict[agent][3] = str(agent_descriptor_dict[agent][3])
        
        ## param: array to tuple and str to None
        if type(agent_descriptor_dict[agent][4]) == list:
            tup = ()
            for i in agent_descriptor_dict[agent][4]:
                tup = tup + (i,)
            
            agent_descriptor_dict[agent][4] = tup
        elif agent_descriptor_dict[agent][4] == 'null' or \
        agent_descriptor_dict[agent][4] == 'None':
            agent_descriptor_dict[agent][4] = None
        
        ## state: str to None
        if agent_descriptor_dict[agent][5] == 'null' or \
        agent_descriptor_dict[agent][5] == 'None':
            agent_descriptor_dict[agent][5] = None
        
        ## Add last value, "call_streams"
        agent_descriptor_dict[agent].append([])
            
        copy[agent] = agent_descriptor_dict[str(agent)]
        
    return copy, json_data['stream_names_tuple']
    
    
'''
# STEP 1
# PROVIDE CODE OR IMPORT PURE (NON-STREAM) FUNCTIONS

from random import randint
def rand(f_args):
    max_integer = f_args[0]
    return randint(0, max_integer)

#def split(m, f_args):
#    divisor = f_args[0]
#    return [_no_value, m] if m%divisor else [m, _no_value]

#def print_value(v, index):
#        #print name + '[' , index , '] = ', v
#        print '[' , index , '] = ', v
#        return (index+1)
'''

'''
# STEP 2
# SPECIFY THE NETWORK.
def make_js_seq(instance_dict, json_file_name):
   
    # Specify names of all the streams.
    #stream_names_tuple = ('random_stream', 'multiples_stream', 'non_multiples_stream')
    #stream_names_tuple = ('generate_stream_of_random_integers_PORT_output', 'split_stream_PORT_multiples', 'split_stream_PORT_nonmultiples')
    
    # Specify the agents:
    # key: agent name
    # value: list of input streams, list of output streams, function, function type,
    #        tuple of arguments, states
    #
    #agent_descriptor_dict = make_agent_descriptor_dict(instance_dict, comp_list)

   
    #agent_descriptor_dict = {
    #    'generate_stream_of_random_integers': [
    #        [], ['generate_stream_of_random_integers_PORT_output'], generate_of_random_integers, 'element', (100,), None],
    #    'split_stream': [
    #        ['generate_stream_of_random_integers_PORT_output'], ['split_stream_PORT_multiples', 'split_stream_PORT_nonmultiples'],
    #        split, 'element', (2,), None],
    #    'print_value_stream': [
    #        ['generate_stream_of_random_integers_PORT_output'], [], print_value, 'element', None, 0],
    #    'print_value_stream1': [['split_stream_PORT_multiples'], [], print_value, 'element', None, 0],
    #    'print_value_stream2': [['split_stream_PORT_nonmultiples'], [], print_value, 'element', None, 0]
    #}
    
    
    
    comp_list = make_comp_list(instance_dict)
    my_json_file_name = make_my_JSON(instance_dict, comp_list)
    
    ## Make agent_descriptor_dict, stream_names_tuple
    agent_descriptor_dict, stream_names_tuple = JSON_to_descriptor_dict_and_stream_names(my_json_file_name)
    #agent_descriptor_dict = test(instance_dict, comp_list)
    #stream_names_tuple = make_stream_names_tuple(instance_dict, comp_list)
        
    
    print('---------agent_descriptor_dict-------')
    pprint(agent_descriptor_dict)
    print('---------stream_names_tuple-------')
    pprint(stream_names_tuple)
    
    # STEP 3: MAKE THE NETWORK
    stream_dict, agent_dict, t_dict = make_network(
        stream_names_tuple, agent_descriptor_dict)
    print('------stream_dict_-------')
    pprint(stream_dict)
    ## # Only for debugging
    ## for key, value in s_dict.items():
    ##     print 'stream name', key
    ##     print 'stream', value

    ## for key, value in a_dict.items():
    ##     print 'agent name', key
    ##     print 'agent', value

    ## for key, value in t_dict.items():
    ##     print 'timer name is', key
    ##     print 'timer', value

    # STEP 4: DRIVE THE NETWORK BY APPENDING
    #      VALUES TO TIMER STREAMS
    
    ## AND ALSO MAKE STRINGS TO BE WRITTEN TO OUTPUT FILE
    
    
    # val_str is a list of values of each time step,
    # concatnated in one long, comma separated string
    val_str = str()
    
    # list of the streams in order
    streams_list = []
    streams_list_done = False
    
    # Doesn't work for copies of streams:
    #    it gives 3 names, even when 1 was called twice
    # Create a list of stream names for the JS file
    #for stream_name in stream_names_tuple:
        # Create list of all streams at each time step
        #streams_list.append(stream_name)
    #print '-----------streams_list-------------'
    #pprint(streams_list)
    
    for t in range(5):
        print '--------- time step: ', t
        # Append t to each of the timer streams
        for stream in t_dict.values():
            print '-------', stream.name
            stream.append(t)
            ## for stream in stream_dict.values():
            ##     stream.print_recent()

            # Print messages in transit to the input port
            # of each agent.
            for agent_name, agent in agent_dict.iteritems():
                descriptor = agent_descriptor_dict[agent_name]
                input_stream_list = descriptor[0]
                for stream_name in input_stream_list:
                    print '--------input_stream_list: ', input_stream_list
                    # Create list of all streams at each time step
                    if streams_list_done == False:
                        streams_list.append(stream_name)
                    
                    # Get the correct stream object
                    stream = stream_dict[stream_name]
                    
                    # value is a string of this form:
                    # [4]
                    value = str(stream.recent[stream.start[agent]:stream.stop])
                    #print '----value------'
                    #print value[1:-1]
                    val_str = val_str + '\'' + value[1:-1] + '\' ,'
                    #val_str = val_str + index_and_value.split(' = ')[1] + ','
                    
                    print "messages in ", stream_name, "to", agent.name
                    print stream.recent[stream.start[agent]:stream.stop]
            streams_list_done = True

    val_str = 'var value = [' + val_str[:-1] + '];'
    
    # stream_str is a list of all streams, 
    # selector_str is the list of streams, but formatted 
    # to be used as selectors in JS
    stream_str = str()
    selector_str = str()
    for s in streams_list:
        selector_str = selector_str + '\'edge[stream= "' + s + '"]\', '
        stream_str = stream_str + '\'' + s + '\', '
    selector_str = 'var edge = [' + selector_str[:-1] + '];'
    stream_str = 'var stream_names = [' + stream_str[:-1] + '];'
    
    
    pprint(stream_str + '\n' +  selector_str + '\n' + val_str)
    return stream_str + '\n' +  selector_str + '\n' + val_str
## t_dict['generate_random'].append(0)
## s_dict['random_stream'].print_recent()
## s_dict['multiples_stream'].print_recent()
## s_dict['non_multiples_stream'].print_recent()

## t_dict['split'].append(1)
## s_dict['random_stream'].print_recent()
## s_dict['multiples_stream'].print_recent()
## s_dict['non_multiples_stream'].print_recent()
'''

#if __name__ == '__main__':
#    main()
    


    
    
