import math
import random
import os
import argparse
import logging
from multiprocessing import Process
from dnd_auction_game import AuctionGameClient

# Configure logging
logging.basicConfig(level=logging.CRITICAL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

############################################################################################
#
# advanced_bidder
#   A more advanced bidding agent with configurable parameters for simulation.
#
############################################################################################

def calculate_expected_value(die: int, num: int, bonus: int) -> float:
    """Calculate the expected value of a dice roll.

    Args:
        die (int): The number of sides on the die.
        num (int): The number of dice being rolled.
        bonus (int): Any bonus added to the roll.

    Returns:
        float: The expected value of the roll.
    """
    average_roll = num * (die + 1) / 2 + bonus
    logger.debug(f"Calculated expected value: die={die}, num={num}, bonus={bonus}, expected_value={average_roll}")
    return average_roll

def advanced_bid(*args, aggressiveness: float = 0.5, risk_tolerance: float = 0.5, point_to_pool: float = 0.5):
    """Advanced bidding function that supports both the old (6 args) and new (8 args)
    callback signatures from the game client:
    - Old: (agent_id, current_round, states, auctions, prev_auctions, bank_state)
    - New: (agent_id, current_round, states, auctions, prev_auctions, pool, prev_pool_buys, bank_state)

    We accept both styles via *args and then parse out pool and prev_pool_buys when present.
    The function returns a dict compatible with the server, e.g. { 'bids': {..}, 'pool': n }.
    """
    # Parse positional args and handle both server signatures
    agent_id = None
    current_round = 0
    states = {}
    auctions = {}
    prev_auctions = {}
    bank_state = {}
    pool_arg = 0
    prev_pool_buys = {}
    # Assign first 5 fixed args
    if len(args) >= 5:
        agent_id = args[0]
        current_round = args[1]
        states = args[2]
        auctions = args[3]
        prev_auctions = args[4]
    # If user passed new signature, parse pool and prev_pool_buys
    if len(args) == 8:
        pool_arg = args[5]
        prev_pool_buys = args[6]
        bank_state = args[7]
    elif len(args) == 6:
        # old signature: 6th arg is bank_state
        bank_state = args[5]
    elif len(args) > 0 and isinstance(args[-1], dict):
        # best-effort fallback
        bank_state = args[-1]
    logger.info(f"Agent {agent_id} - Round {current_round}: Starting bid calculation")
    agent_state = states.get(agent_id, {})
    current_gold = int(agent_state.get("gold", 0))
    logger.info(f"Agent {agent_id} - Current gold: {current_gold}")

    # Bank interest evaluation
    current_interest = bank_state.get("remainder_bank_interest", [1.0])[0]
    logger.info(f"Agent {agent_id} - Current interest: {current_interest}")

    # Decide pool contribution - random but sensible and at least 1 point if we have >0 gold
    pool_contribution_min = 1
    pool_contribution_max = min(5, max(1, int(point_to_pool * 0.2))) if current_gold > 0 else 0
    pool_contribution = random.randint(pool_contribution_min, pool_contribution_max) if pool_contribution_max >= pool_contribution_min else pool_contribution_min

    # Adjust maximum bid based on aggressiveness and reserved pool contribution
    available_for_bids = max(0, current_gold - pool_contribution)
    max_bid = int(available_for_bids * aggressiveness)
    logger.info(f"Agent {agent_id} - max_bid={max_bid}")

    # Evaluate auctions based on the new scoring formula
    auction_values = []
    for auction_id, auction_details in auctions.items():
        die = auction_details["die"]
        num = auction_details["num"]
        bonus = auction_details["bonus"]

        # Calculate mean value and potential yield
        mean_value = num * (die + 1) / 2 + bonus
        # Skip auctions with non-positive expected value
        if mean_value <= 0:
            logger.debug(f"Skipping auction {auction_id} with non-positive mean_value={mean_value}")
            continue
        potential_yield = max(0, num * die + bonus)

        # Calculate auction score based on the formula: mean^(1-risk) + potential^(risk)
        score = (mean_value ** (1 - risk_tolerance)) + (potential_yield ** risk_tolerance)

        # Add auction details to the list for sorting
        auction_values.append({
            "auction_id": auction_id,
            "mean_value": mean_value,
            "potential_yield": potential_yield,
            "score": score,
            "details": auction_details
        })
        logger.debug(f"Agent {agent_id} - Auction {auction_id}: mean_value={mean_value}, potential_yield={potential_yield}, score={score}")

    # Sort auctions by score (descending)
    auction_values.sort(key=lambda x: x["score"], reverse=True)
    logger.info(f"Agent {agent_id} - Sorted auctions by score")

    # Generate bids
    bids = {}
    for auction in auction_values:
        auction_id = auction["auction_id"]
        mean_value = auction["mean_value"]

        # Calculate bid based on mean value and aggressiveness
        bid = abs(min(max_bid, int(mean_value * aggressiveness * 100) + 1))
        logger.info(f"Agent {agent_id} - Auction {auction_id}: Calculated bid={bid}, max_bid={max_bid}")

        # Ensure the agent has enough gold to place the bid
        if available_for_bids - bid >= 0:
            bids[auction_id] = bid
            available_for_bids -= bid
            logger.info(f"Agent {agent_id} - Placed bid on auction {auction_id}: bid={bid}, remaining_gold={current_gold}")
        else:
            logger.warning(f"Agent {agent_id} - Not enough gold to bid on auction {auction_id}: bid={bid}, current_gold={current_gold}")
            break  # Stop bidding if no gold is left

    logger.info(f"Agent {agent_id} - Generated bids: {bids}")
    logger.info(f"Agent {agent_id} - Round {current_round}: Finished bid calculation")
    # Ensure we never ask to contribute more to the pool than remaining gold
    spent_on_bids = sum(bids.values())
    if pool_contribution + spent_on_bids > int(agent_state.get("gold", 0)):
        # Reduce pool contribution to what's left or zero
        pool_contribution = max(0, int(agent_state.get("gold", 0)) - spent_on_bids)

    # Return in server expected format
    return {"bids": bids, "pool": pool_contribution}

def run_agent(host, port, agent_name, player_id, aggressiveness, risk_tolerance, point_to_pool):
    logger.info(f"Starting agent {agent_name} with aggressiveness={aggressiveness}, risk_tolerance={risk_tolerance}, point_to_pool={point_to_pool}")
    game = AuctionGameClient(host=host, agent_name=agent_name, player_id=player_id, port=port)
    try:
        game.run(lambda *args: advanced_bid(*args, aggressiveness=aggressiveness, risk_tolerance=risk_tolerance, point_to_pool=point_to_pool))
    except KeyboardInterrupt:
        logger.info(f"<interrupt - shutting down {agent_name}>")

    logger.info(f"<game is done for {agent_name}>")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run advanced bidding agents for simulation.")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--num_agents", type=int, default=15, help="Number of agents to spin up")
    parser.add_argument("--player_id", type=str, default="id_of_human_player", help="Player ID")

    args = parser.parse_args()

    # # if args.num_agents == 1:
    # aggressiveness = 0.25
    # risk_tolerance = 0.43
    # point_to_pool = 33
    # agent_name = "DoomGuy666_dumb"
    # player_id = "Albert Salvesen-Oroe"
    # host = "opentsetlin.com"
    # port = "8000"
    # run_agent(
    #     args.host,
    #     args.port,
    #     agent_name,
    #     player_id,
    #     aggressiveness,
    #     risk_tolerance,
    #     point_to_pool
    # )
    # # else:
    
    processes = []
    for i in range(args.num_agents):
        # Assign random values if aggressiveness or risk_tolerance is None
        aggressiveness = random.uniform(0.1, 1.0)
        risk_tolerance = random.uniform(0.1, 1.0)
        point_to_pool = random.randint(1, 100)

        agent_name = f"advanced_agent_{point_to_pool}_{int(aggressiveness*100)}_{int(risk_tolerance*100)}"
        p = Process(target=run_agent, args=(
            args.host,
            args.port,
            agent_name,
            args.player_id,
            aggressiveness,
            risk_tolerance,
            point_to_pool
        ))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()