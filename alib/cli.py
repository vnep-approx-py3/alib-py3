# MIT License
#
# Copyright (c) 2016-2017 Matthias Rost, Elias Doehne, Tom Koch, Alexander Elvers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import pickle
import yaml
import click
import itertools

from . import evaluation, run_experiment, scenariogeneration, solutions, util, datamodel

REQUIRED_FOR_PICKLE = solutions  # this prevents pycharm from removing this import, which is required for unpickling solutions


@click.group()
def cli():
    pass


@cli.command()
@click.argument('codebase_id')
@click.argument('remote_base_dir', type=click.Path())
@click.option('--local_base_dir', type=click.Path(exists=True), default=".")
@click.argument('servers')
@click.option('--extra', '-e', multiple=True, type=click.File())
def deploy_code(codebase_id, remote_base_dir, local_base_dir, servers, extra):
    f_deploy_code(codebase_id, remote_base_dir, local_base_dir, servers, extra)


def f_deploy_code(codebase_id, remote_base_dir, local_base_dir, servers, extra):
    """
    Deploys the codebase on a remote server.

    This function is separated from deploy_code so that it can be reused when extending the CLI from outside the alib.

    :param codebase_id:
    :param remote_base_dir:
    :param local_base_dir:
    :param servers:
    :param extra:
    :return:
    """
    click.echo('Deploy codebase')
    if not local_base_dir:
        local_base_dir = os.path.abspath("../../")
    local_base_dir = os.path.abspath(local_base_dir)
    deployer = util.CodebaseDeployer(
        code_base_id=codebase_id,  # string, some unique codebase id
        remote_base_dir=remote_base_dir,  # server path object specifying paths for codebase
        local_base_path=local_base_dir,  # local root directory of the codebase
        servers=servers.split(","),  # servers to deploy to
        cleanup=True,  # delete auto-generated files?
        extra=extra
    )
    deployer.deploy_codebase()


@cli.command()
@click.argument('scenario_output_file')
@click.argument('parameters', type=click.File('r'))
@click.option('--threads', default=1)
def generate_scenarios(scenario_output_file, parameters, threads):
    f_generate_scenarios(scenario_output_file, parameters, threads)


def f_generate_scenarios(scenario_output_file, parameter_file, threads):
    """
    Generates the scenarios according to the scenario parameters found in the parameter_file.

    This function is separated from generate_scenarios so that it can be reused when extending the CLI from outside
    the alib.

    :param scenario_output_file: path to pickle file to which the resulting scenarios will be written
    :param parameter_file: readable file object containing the scenario parameters in yml format
    :param threads: number of concurrent threads used for scenario generation
    :return:
    """
    click.echo('Generate Scenarios')
    util.ExperimentPathHandler.initialize()
    file_basename = os.path.basename(parameter_file.name).split(".")[0].lower()
    log_file = os.path.join(util.ExperimentPathHandler.LOG_DIR, "{}_scenario_generation.log".format(file_basename))
    util.initialize_root_logger(log_file)
    scenariogeneration.generate_pickle_from_yml(parameter_file, scenario_output_file, threads)


@cli.command()
@click.argument('dc_baseline', type=click.File('r'))
@click.argument('dc_randround', type=click.File('r'))
def full_evaluation(dc_baseline, dc_randround):
    baseline_data = pickle.load(dc_baseline)
    randround_data = pickle.load(dc_randround)
    evaluation.plot_heatmaps(baseline_data, randround_data)


@cli.command()
@click.argument('pickle_file', type=click.File('r'))
@click.option('--col_output_limit', default=None)
def pretty_print(pickle_file, col_output_limit):
    data = pickle.load(pickle_file)
    pp = util.PrettyPrinter()
    print pp.pprint(data, col_output_limit=col_output_limit)

@cli.command()
@click.argument('experiment_yaml', type=click.File('r'))
@click.argument('min_scenario_index', type=click.INT)
@click.argument('max_scenario_index', type=click.INT)
@click.option('--concurrent', default=1)
def start_experiment(experiment_yaml,
                     min_scenario_index, max_scenario_index,
                     concurrent):
    f_start_experiment(experiment_yaml,
                       min_scenario_index, max_scenario_index,
                       concurrent)


def f_start_experiment(experiment_yaml,
                       min_scenario_index, max_scenario_index,
                       concurrent):
    """
    Executes the experiment according to the execution parameters found in the experiment_yaml.

    This function is separated from start_experiment so that it can be reused when extending the CLI from outside
    the alib.

    :param experiment_yaml: readable file object containing the execution parameters in yml format
    :param scenario_output_file: path to pickle file to which the resulting scenarios will be written
    :param threads: number of concurrent threads used for scenario generation
    :return:
    """
    click.echo('Start Experiment')
    util.ExperimentPathHandler.initialize()
    file_basename = os.path.basename(experiment_yaml.name).split(".")[0].lower()
    log_file = os.path.join(util.ExperimentPathHandler.LOG_DIR, "{}_experiment_execution.log".format(file_basename))
    util.initialize_root_logger(log_file)

    run_experiment.run_experiment(
        experiment_yaml,
        min_scenario_index, max_scenario_index,
        concurrent
    )

@cli.command()
@click.argument('yaml_file_with_cacus_request_graph_definition', type=click.Path())
def inspect_cactus_request_graph_generation(yaml_file_with_cacus_request_graph_definition):
    util.ExperimentPathHandler.initialize()
    print(yaml_file_with_cacus_request_graph_definition)
    param_space = None
    with open(yaml_file_with_cacus_request_graph_definition, "r") as f:
        param_space = yaml.load(f)
    print "----------------------"
    print param_space
    print "----------------------"
    for request_generation_task in param_space[scenariogeneration.REQUEST_GENERATION_TASK]:
        for name, values in request_generation_task.iteritems():
            print name, values
            if "CactusRequestGenerator" in values:
                raw_parameters = values["CactusRequestGenerator"]
                print "\n\nextracted the following parameters..."
                print name, ": ", raw_parameters
                f_inspect_specfic_cactus_request_graph_generation_and_output(name, raw_parameters)

def f_inspect_specfic_cactus_request_graph_generation_and_output(name, raw_parameters):
    simple_substrate = datamodel.Substrate("stupid_simple")
    simple_substrate.add_node("u", ["universal"], capacity={"universal": 1000}, cost=1000)
    simple_substrate.add_node("v", ["universal"], capacity={"universal": 1000}, cost=1000)
    simple_substrate.add_edge("u", "v", capacity=1000, cost=1000, bidirected=True)

    iterations = 500000
    # flatten values
    param_key_list = []
    param_value_list = []
    for key, value in raw_parameters.iteritems():
        param_key_list.append(key)
        param_value_list.append(value)

    import numpy as np
    import matplotlib.pyplot as plt

    def ecdf(x):
        xs = np.sort(x)
        ys = np.arange(1, len(xs) + 1) / float(len(xs))
        return xs, ys


    for param_combo_index, param_combo in enumerate(itertools.product(*param_value_list)):
        flattended_raw_parameters = {}
        for index, value in enumerate(param_combo):
            flattended_raw_parameters[param_key_list[index]] = value

        print flattended_raw_parameters
        cactus_generator = scenariogeneration.CactusRequestGenerator()

        advanced_information = cactus_generator.advanced_empirical_number_of_nodes_edges(flattended_raw_parameters, simple_substrate,iterations)

        min_nodes = flattended_raw_parameters["min_number_of_nodes"]
        max_nodes = flattended_raw_parameters["max_number_of_nodes"]

        edge_count_per_node = {node_number : [] for node_number in range(min_nodes, max_nodes+1)}

        node_numbers = []
        edge_numbers = []

        max_edge_count = 0
        for node, edge in advanced_information.node_edge_comination:
            edge_count_per_node[node].append(edge)
            if edge > max_edge_count:
                max_edge_count = edge
            node_numbers.append(node)
            edge_numbers.append(edge)

        fig = plt.figure(figsize=(8,12))
        ax = plt.subplot(111)

        for node_number in range(min_nodes, max_nodes+4):
            if node_number == max_nodes + 1:
                xs, ys = ecdf(node_numbers)
                xs = np.insert(xs, 0, min_nodes, axis=0)
                xs = np.insert(xs, 0, min_nodes - 1, axis=0)
            elif node_number == max_nodes + 2:
                xs, ys = ecdf(edge_numbers)
                xs = np.insert(xs, 0, min_nodes, axis=0)
                xs = np.insert(xs, 0, min_nodes-1, axis=0)
            elif node_number == max_nodes + 3:
                xs, ys = ecdf(advanced_information.generated_cycles)
                xs = np.insert(xs, 0, 1, axis=0)
                xs = np.insert(xs, 0, 0, axis=0)
            else:
                if len(edge_count_per_node[node_number]) == 0:
                    continue
                xs, ys = ecdf(edge_count_per_node[node_number])
                xs = np.insert(xs, 0, min(edge_count_per_node[node_number]), axis=0)
                xs = np.insert(xs, 0, min(edge_count_per_node[node_number]) - 1, axis=0)

            xs = np.append(xs, max_edge_count+1)
            ys = np.insert(ys, 0, 0, axis=0)
            ys = np.insert(ys, 0, 0, axis=0)
            ys = np.append(ys, 1.0)
            #print node_number, xs, ys
            #print xs, ys
            print "plot ....", node_number
            label = "edge_count_per_node_count_{}".format(node_number)
            if node_number == max_nodes + 1:
                label = "node_count"
            if node_number == max_nodes + 2:
                label = "edge_count"
                print xs[0:10], ys[0:10]
            if node_number == max_nodes + 3:
                label = "cycle_count"
            if node_number <= max_nodes:
                ax.step(xs, ys, label=label, linestyle="-.")
            else:
                ax.step(xs, ys, label=label, linestyle="-")

        title = "\n".join(["{}: {}".format(key, value) for key, value in flattended_raw_parameters.iteritems()])
        title += "\n\nExp. |V|: {}; Exp. |E|: {}; Exp. |C|: {}; Exp. CC: {}\n\n".format(
            advanced_information.nodes_generated / float(iterations),
            advanced_information.edges_generated / float(iterations),
            sum(advanced_information.generated_cycles) / float(iterations),
            advanced_information.overall_cycle_edges / float(advanced_information.edges_generated))
        title += "failed generation attempts: {}%\n".format(advanced_information.generation_tries_failed/float(advanced_information.generation_tries_overall)*100.0)
        title += "overall iterations: {}".format(iterations)

        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                  fancybox=True, shadow=True, ncol=2)
        plt.title(title)
        plt.xticks(range(0,max_edge_count+1))
        plt.tight_layout()
        #plt.show()
        filename= util.ExperimentPathHandler.OUTPUT_DIR + "/{}_{}.pdf".format(name, param_combo_index)
        print filename
        plt.savefig(filename, dpi=300)


        # overall_cycle_edges /= float(total_edges)
        # total_nodes /= float(iterations)
        # total_edges /= float(iterations)
        #
        # print("Expecting {} nodes, {} edges, {}% edges on cycle".format(total_nodes, total_edges,
        #                                                                 overall_cycle_edges * 100))

        #print edge_count_per_node


if __name__ == '__main__':
    cli()
