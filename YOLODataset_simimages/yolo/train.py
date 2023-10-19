#! /usr/bin/env python

from __future__ import division

import os
import tqdm
import argparse

import torch
from torch.utils.data import DataLoader
import torch.optim as optim

from models import load_model
from utils.utils import load_classes, result_visualize
from utils.datasets import ListDataset
from utils.transforms import DEFAULT_TRANSFORMS
from utils.augmentations import AUGMENTATION_TRANSFORMS
from utils.loss import compute_loss
from test import _evaluate, _create_validation_data_loader

from utils.parse_config import parse_data_config

def _create_data_loader(img_path, batch_size, img_size, num_workers, multiscale_training=False):
    """Creates a DataLoader for training.
    :param img_path: Path to file containing all paths to training images.
    :type img_path: str
    :param batch_size: Size of each image batch
    :type batch_size: int
    :param img_size: Size of each image dimension for yolo
    :type img_size: int
    :param n_cpu: Number of cpu threads to use during batch generation
    :type n_cpu: int
    :param multiscale_training: Scale images to different sizes randomly
    :type multiscale_training: bool
    :return: Returns DataLoader
    :rtype: DataLoader
    """
    dataset = ListDataset(
        img_path,
        img_size=img_size,
        multiscale=multiscale_training,
        transform=AUGMENTATION_TRANSFORMS
        )
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        shuffle=True,
        pin_memory=True,
        collate_fn=dataset.collate_fn,)
    return dataloader

def run():
    parser = argparse.ArgumentParser(description="Trains the YOLO model.")
    parser.add_argument("-m", "--model", type=str, default="config/yolov3-tiny.cfg", help="Path to model definition file (.cfg)")
    parser.add_argument("-d", "--data", type=str, default="config/Ball.data", help="Path to data config file (.data)")
    parser.add_argument("-e", "--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("-v", "--verbose", action='store_true', help="Makes the training more verbose")
    parser.add_argument("--n_cpu", type=int, default=8, help="Number of cpu threads to use during batch generation")
    parser.add_argument("--pretrained_weights", type=str, default="weights/yolov3-tiny.weights", help="Path to checkpoint file (.weights or .pth). Starts training from checkpoint model")
    parser.add_argument("--checkpoint_interval", type=int, default=1, help="Interval of epochs between saving model weights")
    parser.add_argument("--evaluation_interval", type=int, default=1, help="Interval of epochs between evaluations on validation set")
    parser.add_argument("--iou_thres", type=float, default=0.5, help="Evaluation: IOU threshold required to qualify as detected")
    parser.add_argument("--conf_thres", type=float, default=0.7, help="Evaluation: Object confidence threshold")
    parser.add_argument("--nms_thres", type=float, default=0.4, help="Evaluation: IOU threshold for non-maximum suppression")
    args = parser.parse_args()
    print("Command line arguments: {}".format(args))

    data_config = parse_data_config(args.data)
    train_path = data_config["train"]
    valid_path = data_config["valid"]
    class_names = load_classes(data_config["names"])

    if not os.path.isdir("checkpoints"):
        os.makedirs("checkpoints")
    if not os.path.isdir("train_results"):
        os.makedirs("train_results")
    
    model = load_model(args.model, args.pretrained_weights)
    mini_batch_size = model.hyperparams['batch'] // model.hyperparams['subdivisions']
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # #################
    # Create Dataloader
    # #################

    # Load training dataloader
    dataloader = _create_data_loader(
        train_path,
        mini_batch_size,
        model.hyperparams['height'],
        args.n_cpu)

    # Load validation dataloader
    validation_dataloader = _create_validation_data_loader(
        valid_path,
        mini_batch_size,
        model.hyperparams['height'],
        args.n_cpu)

    # ################
    # Create optimizer
    # ################

    params = [p for p in model.parameters() if p.requires_grad]

    if (model.hyperparams['optimizer'] in [None, "adam"]):
            optimizer = optim.Adam(
                params,
                lr=model.hyperparams['learning_rate'],
                weight_decay=model.hyperparams['decay'],
            )
    else:
        print("Unknown optimizer. Please choose between (adam, sgd).")

    train_loss_list = []
    lr_list = []
    mAP_list = []

    # skip epoch zero, because then the calculations for when to evaluate/checkpoint makes more intuitive sense
    # e.g. when you stop after 30 epochs and evaluate every 10 epochs then the evaluations happen after: 10,20,30
    # instead of: 0, 10, 20
    
    for epoch in range(1, args.epochs+1):

        print("\n---- Training Model ----")

        train_loss = []
        model.train()  # Set model to training mode
        for batch_i, (_, imgs, targets) in enumerate(tqdm.tqdm(dataloader, desc="Training Epoch {}".format(epoch))):
            
            batches_done = len(dataloader) * epoch + batch_i

            imgs = imgs.to(device, non_blocking=True)
            targets = targets.to(device)

            outputs = model(imgs)

            loss, loss_components = compute_loss(outputs, targets, model)

            loss.backward()

            train_loss.append(loss.item())

            ###############
            # Run optimizer
            ###############

            if batches_done % model.hyperparams['subdivisions'] == 0:
                # Adapt learning rate
                # Get learning rate defined in cfg
                lr = model.hyperparams['learning_rate']
                if batches_done < model.hyperparams['burn_in']:
                    # Burn in
                    lr *= (batches_done / model.hyperparams['burn_in'])
                else:
                    # Set and parse the learning rate to the steps defined in the cfg
                    for threshold, value in model.hyperparams['lr_steps']:
                        if batches_done > threshold:
                            lr *= value

                for g in optimizer.param_groups:
                    g['lr'] = lr
                
                # Run optimizer
                optimizer.step()
                # Reset gradients
                optimizer.zero_grad()

            model.seen += imgs.size(0)

        # #############
        # Save progress
        # #############

        # Save model weight to checkpoint file
        if epoch % args.checkpoint_interval == 0:
            checkpoint_path = "checkpoints/yolov3_ckpt_{}.pth".format(epoch)
            print("---- Saving checkpoint to: '{}' ----".format(checkpoint_path))
            torch.save(model.state_dict(), checkpoint_path)
        
        train_loss_list.append(sum(train_loss)/len(train_loss))
        lr_list.append(lr)

        # ########
        # Evaluate
        # ########
        
        if epoch % args.evaluation_interval == 0:
            print("\n---- Evaluating Model ----")
            # Evaluate the model on the validation set
            metrics_output = _evaluate(
                model,
                validation_dataloader,
                class_names,
                img_size=model.hyperparams['height'],
                iou_thres=args.iou_thres,
                conf_thres=args.conf_thres,
                nms_thres=args.nms_thres,
                verbose=args.verbose
            )
        _, _, AP, _, _ = metrics_output
        mAP_list.append(AP.mean())
    result_visualize(train_loss_list, lr_list, mAP_list)


if __name__ == "__main__":
    run()
