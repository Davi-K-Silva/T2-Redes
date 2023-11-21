import dash 
from dash.dependencies import Output, Input, State
from dash import dcc
from dash import html
from dash import dash_table
import plotly 
import plotly.graph_objs as go 
from collections import deque 
import time
from pysnmp.hlapi import *
from pysnmp.hlapi import varbinds
import pysnmp.hlapi.varbinds
import pandas as pd
import sys

# SNMP parameters
community_string = ''
host = ''
port = 161
refreshRate = 0

correctNum = 34

if "-correct:" in sys.argv:
    correctNum = int(sys.argv[2])

def get_snmp_data_OID(host, port, community, OID):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((host, port)),
        ContextData(),
        ObjectType(ObjectIdentity(OID))
    )

    error_indication, error_status, error_index, var_binds = next(iterator)

    if error_indication:
        print(error_indication)
        return None
    elif error_status:
        print('%s at %s' % (
            error_status.prettyPrint(),
            error_index and var_binds[int(error_index) - 1][0] or '?'
        ))
        return None
    else:
        for var_bind in var_binds:
            # print(type(var_bind[1]))
            if type(var_bind[1]).__name__ == "DisplayString":
                return str(var_bind[1])
            else:
                return int(var_bind[1])


def get_snmp_data(host, port, community, MIB, target , targetNum):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((host, port)),
        ContextData(),
        ObjectType(ObjectIdentity(MIB, target, targetNum))
    )

    error_indication, error_status, error_index, var_binds = next(iterator)

    if error_indication:
        print(error_indication)
        return None
    elif error_status:
        print('%s at %s' % (
            error_status.prettyPrint(),
            error_index and var_binds[int(error_index) - 1][0] or '?'
        ))
        return None
    else:
        for var_bind in var_binds:
            # print(type(var_bind[1]).__name__)
            if type(var_bind[1]).__name__ == "DisplayString":
                return str(var_bind[1])
            else:
                return int(var_bind[1])


### ---------------------------------------------------------------------------------------- ###
# Metrics Calculation functions

# porcentagem de pacotes recebidos com erro
def packageInError():
    inErrors =  get_snmp_data(host, port, community_string,"IF-MIB", "ifInErrors",1)
    inUcastPkts = get_snmp_data(host, port, community_string,"IF-MIB", "ifInUcastPkts",1)
    InNUCastPkts = get_snmp_data(host, port, community_string,"IF-MIB", "ifInNUcastPkts",1)

    return (inErrors / (inUcastPkts + InNUCastPkts))

# taxa de bytes/segundo
def byteRate():
    global previousInOctets
    global previousOutOctets
    inOctets = get_snmp_data(host, port, community_string,"IF-MIB", "ifInOctets",correctNum)
    outOctets = get_snmp_data(host, port, community_string,"IF-MIB", "ifOutOctets",correctNum)
    previousInOctetsInt = previousInOctets[-1]
    previousOutOctetsInt = previousOutOctets[-1]
    previousTime = XBytes[-1]
    currentTime = time.time()
    previousInOctets.append(inOctets)
    previousOutOctets.append(outOctets)

    return ((inOctets + outOctets) - (previousInOctetsInt + previousOutOctetsInt))/max(1, (currentTime - previousTime))

# utilizacao do link
def linkUsage():
    byteRate = YBytes[-1]
    speed = get_snmp_data(host, port, community_string,"IF-MIB", "ifSpeed",correctNum)
    
    return (byteRate * 8)/speed

# porcentagem de datagramas IP recebidos com erro
def datagramInError():
    inHDRErros = get_snmp_data(host, port, community_string,"IP-MIB", "ipInHdrErrors",0)
    inAddrErrors = get_snmp_data(host, port, community_string,"IP-MIB", "ipInAddrErrors",0)
    inUnknowProtos = get_snmp_data(host, port, community_string,"IP-MIB", "ipInUnknownProtos",0)
    inReceives = get_snmp_data(host, port, community_string,"IP-MIB", "ipInReceives",0)
    return (inHDRErros + inAddrErrors + inUnknowProtos)/inReceives

# taxa de forwarding/segundo
def ipForwardingRate():
    global previousForwDatagrams
    currentForwDatagrams = get_snmp_data(host, port, community_string,"IP-MIB", "ipForwDatagrams",0)
    previousForwDatagramsInt = previousForwDatagrams[-1]
    previousTime = XForwards[-1]
    currentTime = time.time()
    previousForwDatagrams.append(previousForwDatagramsInt)
    return (currentForwDatagrams-previousForwDatagramsInt)/(currentTime-previousTime)
### ---------------------------------------------------------------------------------------- ###
# DASH

#Packets queue
XPackets = deque(maxlen = 20) 
#XPackets.append(time.time()) 

YPackets = deque(maxlen = 20) 
#YPackets.append(packageInError()) 

##Bytes queue
XBytes = deque(maxlen = 20) 
#XBytes.append(time.time())

YBytes = deque(maxlen = 20) 

previousInOctets = deque(maxlen = 20)
#previousInOctets.append(0)
previousOutOctets = deque(maxlen = 20)
#previousOutOctets.append(0)

#YBytes.append(byteRate()) 

##Link queue
XLink = deque(maxlen = 20) 
#XLink.append(time.time())

YLink = deque(maxlen = 20) 
#YLink.append(linkUsage()) 

##Datagrams queue
XDatagrams = deque(maxlen = 20) 
#XDatagrams.append(time.time())

YDatagrams = deque(maxlen = 20) 
#YDatagrams.append(datagramInError()) 


#Forwarding queue
XForwards = deque(maxlen = 20) 
#XForwards.append(time.time())

previousForwDatagrams = deque(maxlen = 20) 
#previousForwDatagrams.append(0)

YForwards = deque(maxlen = 20) 
#YForwards.append(ipForwardingRate()) 


d = {}

df = pd.DataFrame(data=d)

app = dash.Dash(__name__, suppress_callback_exceptions=True) 

app.layout = html.Div(className='row', children=[
    html.H1("SNMP Monitoring Dashboard"),
    html.Label("Enter SNMP Device Information:"),
    dcc.Input(id='input-ip', type='text', placeholder='Enter IP address', style={'marginBottom': 10}),
    dcc.Input(id='input-community', type='text', placeholder='Enter community string', style={'marginBottom': 10}),
    dcc.Input(id='input-refresh-rate', type='number', placeholder='Enter refresh rate (seconds)', style={'marginBottom': 10}),
    html.Button('Start Monitoring', id='btn-start-monitoring', n_clicks=0),
    html.Div( id = "block1"),
    html.Div( id = "block2"),
    html.Div( id = "block3"),
    # html.Div( children=
    # [   
    #     dash_table.DataTable(df.to_dict('records')),
    #     dcc.Graph(id = 'live-graph3', animate = True,style={'display': 'inline-block'}), 
    #     dcc.Interval( 
    #         id = 'graph-update3', 
    #         interval = refreshRate, 
    #         n_intervals = 0
    #     ), 
    #     dcc.Graph(id = 'live-graph2', animate = True,style={'display': 'inline-block'}), 
    #     dcc.Interval( 
    #         id = 'graph-update2', 
    #         interval = refreshRate, 
    #         n_intervals = 0
    #     ) 
    # ]) ,
    # html.Div( 
    # [
    #     dcc.Graph(id = 'live-graph', animate = True,style={'display': 'inline-block'}), 
    #     dcc.Interval( 
    #         id = 'graph-update', 
    #         interval = refreshRate, 
    #         n_intervals = 0
    #     ), 
    #     dcc.Graph(id = 'live-graph4', animate = True,style={'display': 'inline-block'}), 
    #     dcc.Interval( 
    #         id = 'graph-update4', 
    #         interval = refreshRate, 
    #         n_intervals = 0
    #     ) 
    # ]),
    # html.Div( 
    # [ 
    #     dcc.Graph(id = 'live-graph5', animate = True,style={'display': 'inline-block'}), 
    #     dcc.Interval( 
    #         id = 'graph-update5', 
    #         interval = refreshRate, 
    #         n_intervals = 0
    #     ) 
    # ])
])

### ---------------------------------------------------------------------------------------- ###
# Callbacks

@app.callback( 
    Output('live-graph', 'figure'), 
    [ Input('graph-update', 'n_intervals') ] 
) 
def update_graph_scatterPackets(n): 
    
    errorPercentage = packageInError()

    XPackets.append(time.time()) 
    YPackets.append(errorPercentage) 

    data = plotly.graph_objs.Scatter( 
            x=list(XPackets), 
            y=list(YPackets), 
            name='Scatter', 
            mode= 'lines+markers'
    ) 

    return {'data': [data], 
            'layout' : go.Layout(xaxis=dict(range=[min(XPackets),max(XPackets)]),yaxis = dict(range = [min(YPackets),max(YPackets)]),title="Package Error percent")} 



@app.callback( 
    Output('live-graph2', 'figure'), 
    [ Input('graph-update2', 'n_intervals') ] 
) 
def update_graph_scatterBytes(n): 
    XBytes.append(time.time()) 
    YBytes.append(byteRate()) 

    data = plotly.graph_objs.Scatter( 
            x=list(XBytes), 
            y=list(YBytes), 
            name='Scatter', 
            mode= 'lines+markers'
    ) 

    return {'data': [data], 
            'layout' : go.Layout(xaxis=dict(range=[min(XBytes),max(XBytes)]),yaxis = dict(range = [min(YBytes),max(YBytes)]),title="Byte rate /s")} 



@app.callback( 
    Output('live-graph3', 'figure'), 
    [ Input('graph-update3', 'n_intervals') ] 
) 
def update_graph_scatterLink(n): 	
    XLink.append(time.time()) 
    YLink.append(linkUsage()) 

    data = plotly.graph_objs.Scatter( 
            x=list(XLink), 
            y=list(YLink), 
            name='Scatter', 
            mode= 'lines+markers'
    ) 

    return {'data': [data], 
            'layout' : go.Layout(xaxis=dict(range=[min(XLink),max(XLink)]),yaxis = dict(range = [min(YLink),max(YLink)]),title="Link usage")} 



@app.callback( 
    Output('live-graph4', 'figure'), 
    [ Input('graph-update4', 'n_intervals') ] 
) 
def update_graph_scatterDatagrams(n): 	
    XDatagrams.append(time.time()) 
    YDatagrams.append(datagramInError()) 

    data = plotly.graph_objs.Scatter( 
            x=list(XDatagrams), 
            y=list(YDatagrams), 
            name='Scatter', 
            mode= 'lines+markers'
    ) 

    return {'data': [data], 
            'layout' : go.Layout(xaxis=dict(range=[min(XDatagrams),max(XDatagrams)]),yaxis = dict(range = [min(YDatagrams),max(YDatagrams)]),title="Datagram error rate")} 



@app.callback( 
    Output('live-graph5', 'figure'), 
    [ Input('graph-update5', 'n_intervals') ] 
) 
def update_graph_scatterForwarding(n): 	
    XForwards.append(time.time()) 
    YForwards.append(ipForwardingRate()) 

    data = plotly.graph_objs.Scatter( 
            x=list(XForwards), 
            y=list(YForwards), 
            name='Scatter', 
            mode= 'lines+markers'
    ) 

    return {'data': [data], 
            'layout' : go.Layout(xaxis=dict(range=[min(XForwards),max(XForwards)]),yaxis = dict(range = [min(YForwards),max(YForwards)]),title="Forwarding rate")} 

@app.callback(
    [Output('block1', 'children'),
     Output('block2', 'children'),
     Output('block3', 'children')],
    [Input('btn-start-monitoring', 'n_clicks')],
    [State('input-ip', 'value'),
     State('input-community', 'value'),
     State('input-refresh-rate', 'value')]
)
def start_monitoring(n_clicks, ip, community, refresh_rate):
    global host
    global community_string
    global refreshRate
    if n_clicks > 0:

        print(type(ip))
        print(type(community))
        print(type(refresh_rate))


        host = ip
        community_string = community
        refreshRate = refresh_rate

        #Packets queue
        XPackets.append(time.time()) 
        YPackets.append(packageInError()) 

        ##Bytes queue
        XBytes.append(time.time())
 
        previousInOctets.append(0)
        previousOutOctets.append(0)

        YBytes.append(byteRate()) 

        ##Link queue
        XLink.append(time.time())
        YLink.append(linkUsage()) 

        ##Datagrams queue
        XDatagrams.append(time.time())
        YDatagrams.append(datagramInError()) 


        #Forwarding queue
        XForwards.append(time.time())

        previousForwDatagrams.append(0)

        YForwards.append(ipForwardingRate()) 

        d = {   'Field': ['sysName','sysDescr','sysUpTime','ifOperStatus','ifAdminStatus', 'ifDescr'],
                'Value': [get_snmp_data_OID(host, port, community_string,'1.3.6.1.2.1.1.5.0'),
                        get_snmp_data_OID(host, port, community_string,'1.3.6.1.2.1.1.1.0'),
                        get_snmp_data_OID(host, port, community_string,'1.3.6.1.2.1.1.3.0'),
                        get_snmp_data(host, port, community_string,"IF-MIB", "ifOperStatus",1),
                        get_snmp_data(host, port, community_string,"IF-MIB", "ifAdminStatus",1),
                        get_snmp_data(host, port, community_string,"IF-MIB", "ifDescr",1)]
            }

        df = pd.DataFrame(data=d)

        b1 = [   
            dash_table.DataTable(df.to_dict('records')),
            dcc.Graph(id = 'live-graph3', animate = True,style={'display': 'inline-block'}), 
            dcc.Interval( 
                id = 'graph-update3', 
                interval = refreshRate, 
                n_intervals = 0
            ), 
            dcc.Graph(id = 'live-graph2', animate = True,style={'display': 'inline-block'}), 
            dcc.Interval( 
                id = 'graph-update2', 
                interval = refreshRate, 
                n_intervals = 0
            ) 
        ]

        b2 =  [
            dcc.Graph(id = 'live-graph', animate = True,style={'display': 'inline-block'}), 
            dcc.Interval( 
                id = 'graph-update', 
                interval = refreshRate, 
                n_intervals = 0
            ), 
            dcc.Graph(id = 'live-graph4', animate = True,style={'display': 'inline-block'}), 
            dcc.Interval( 
                id = 'graph-update4', 
                interval = refreshRate, 
                n_intervals = 0
            ) 
        ]   

        b3 = [ 
            dcc.Graph(id = 'live-graph5', animate = True,style={'display': 'inline-block'}), 
            dcc.Interval( 
                id = 'graph-update5', 
                interval = refreshRate, 
                n_intervals = 0
            ) 
        ]

        return b1, b2, b3
    return dash.no_update
    

if __name__ == '__main__': 
    app.run_server(host='0.0.0.0', port=8080 ,debug=True)


