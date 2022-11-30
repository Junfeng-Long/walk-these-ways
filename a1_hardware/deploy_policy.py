import glob
import pickle as pkl
import sys

from a1_hardware.a1_utilities.state_estimator import StateEstimator
from a1_hardware.a1_utilities.robot_agent import Agent
from a1_hardware.a1_utilities.deployment_runner import DeploymentRunner
from a1_hardware.a1_utilities.robot_controller import RobotController

import pathlib

controller = RobotController()

def load_and_run_policy(label, experiment_name, probe_policy_label=None, max_vel=1.0, max_yaw_vel=1.0, max_vel_probe=1.0):
    # load agent
    dirs = glob.glob(f"../../runs/{label}/*")
    logdir = sorted(dirs)[0]

    with open(logdir+"/parameters.pkl", 'rb') as file:
        pkl_cfg = pkl.load(file)
        print(pkl_cfg.keys())
        cfg = pkl_cfg["Cfg"]
        print(cfg.keys())

    controller.start_thread()
    se = StateEstimator(controller)

    control_dt = 0.02
    # command_profile = RCControllerProfile(dt=control_dt, state_estimator=se, x_scale=max_vel, y_scale=0.6, yaw_scale=max_yaw_vel, probe_vel_multiplier=(max_vel_probe / max_vel))

    hardware_agent = Agent(cfg, se)

    from a1_hardware.a1_utilities.history_wraper import HistoryWrapper
    hardware_agent = HistoryWrapper(hardware_agent)

    policy = load_policy(logdir)

    if probe_policy_label is not None:
        # load agent
        dirs = glob.glob(f"../runs/{probe_policy_label}_*")
        probe_policy_logdir = sorted(dirs)[0]
        with open(probe_policy_logdir + "/parameters.pkl", 'rb') as file:
            probe_cfg = pkl.load(file)
            probe_cfg = probe_cfg["Cfg"]
        probe_policy = load_policy(probe_policy_logdir)

    # load runner
    root = f"{pathlib.Path(__file__).parent.resolve()}/../../logs/"
    pathlib.Path(root).mkdir(parents=True, exist_ok=True)
    deployment_runner = DeploymentRunner(experiment_name=experiment_name, se=None,
                                         log_root=f"{root}/{experiment_name}")
    deployment_runner.add_control_agent(hardware_agent, "hardware_closed_loop")
    deployment_runner.add_policy(policy)
    if probe_policy_label is not None:
        deployment_runner.add_probe_policy(probe_policy, probe_cfg)
    deployment_runner.add_command_profile(command_profile)

    if len(sys.argv) >= 2:
        max_steps = int(sys.argv[1])
    else:
        max_steps = 10000000
    print(f'max steps {max_steps}')

    deployment_runner.run(max_steps=max_steps, logging=True)
    controller.stop_thread()

def load_policy(logdir):
    body = torch.jit.load(logdir + '/checkpoints/body_latest.jit')
    import os
    adaptation_module = torch.jit.load(logdir + '/checkpoints/adaptation_module_latest.jit')

    def policy(obs, info):
        i = 0
        latent = adaptation_module.forward(obs["obs_history"].to('cpu'))
        action = body.forward(torch.cat((obs["obs_history"].to('cpu'), latent), dim=-1))
        info['latent'] = latent
        return action

    return policy


if __name__ == '__main__':
    label = "gait-conditioned-agility/pretrain-v0/train"

    probe_policy_label = None

    experiment_name = "example_experiment"

    load_and_run_policy(label, experiment_name=experiment_name, probe_policy_label=probe_policy_label, max_vel=3.0, max_yaw_vel=5.0, max_vel_probe=1.0)