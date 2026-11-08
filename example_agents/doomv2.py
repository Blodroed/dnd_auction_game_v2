import argparse
import logging
import random
from dnd_auction_game import AuctionGameClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def advanced_bid(*args, aggressiveness: float = 0.5, risk_tolerance: float = 0.5, point_to_pool: float = 0.5):
    # Support both "old" and "new" callback signatures
    agent_id = None
    current_round = 0
    states = {}
    auctions = {}
    prev_auctions = {}
    bank_state = {}
    pool_arg = 0
    prev_pool_buys = {}

    if len(args) >= 5:
        agent_id, current_round, states, auctions, prev_auctions = args[:5]
    if len(args) == 8:
        pool_arg, prev_pool_buys, bank_state = args[5], args[6], args[7]
    elif len(args) == 6:
        bank_state = args[5]
    elif len(args) > 0 and isinstance(args[-1], dict):
        bank_state = args[-1]

    agent_state = states.get(agent_id, {})
    current_gold = int(agent_state.get("gold", 0))

    pool_contribution_min = 1 if current_gold > 0 else 0
    pool_contribution_max = min(5, max(1, int(point_to_pool * 0.2))) if current_gold > 0 else 0
    pool_contribution = random.randint(pool_contribution_min, pool_contribution_max) if pool_contribution_max >= pool_contribution_min else pool_contribution_min

    available_for_bids = max(0, current_gold - pool_contribution)
    max_bid = int(available_for_bids * aggressiveness)

    auction_values = []
    for auction_id, auction_details in auctions.items():
        die = auction_details.get("die", 0)
        num = auction_details.get("num", 0)
        bonus = auction_details.get("bonus", 0)
        mean_value = num * (die + 1) / 2 + bonus
        if mean_value <= 0:
            continue
        potential_yield = max(0, num * die + bonus)
        score = (mean_value ** (1 - risk_tolerance)) + (potential_yield ** risk_tolerance)
        auction_values.append({
            "auction_id": auction_id,
            "mean_value": mean_value,
            "score": score,
            "details": auction_details
        })

    auction_values.sort(key=lambda x: x["score"], reverse=True)

    bids = {}
    for auction in auction_values:
        auction_id = auction["auction_id"]
        mean_value = auction["mean_value"]
        bid = abs(min(max_bid, int(mean_value * aggressiveness * 100) + 1))
        if available_for_bids - bid >= 0:
            bids[auction_id] = bid
            available_for_bids -= bid
        else:
            break

    spent_on_bids = sum(bids.values())
    if pool_contribution + spent_on_bids > current_gold:
        pool_contribution = max(0, current_gold - spent_on_bids)

    return {"bids": bids, "pool": pool_contribution}


def run_agent(host, port, agent_name, player_id, aggressiveness, risk_tolerance, point_to_pool):
    logger.info(f"Starting agent {agent_name} -> host={host}:{port}, player_id={player_id}, aggressiveness={aggressiveness}, risk_tolerance={risk_tolerance}, point_to_pool={point_to_pool}")
    game = AuctionGameClient(host=host, agent_name=agent_name, player_id=player_id, port=port)
    try:
        game.run(lambda *args: advanced_bid(*args, aggressiveness=aggressiveness, risk_tolerance=risk_tolerance, point_to_pool=point_to_pool))
    except KeyboardInterrupt:
        logger.info(f"<interrupt - shutting down {agent_name}>")

    logger.info(f"<game is done for {agent_name}>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a single advanced bidding agent (single bot).")
    parser.add_argument("--host", type=str, default="opentsetlin.com", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--player_id", type=str, default="Albert Salvesen Oroe", help="Player ID")
    parser.add_argument("--aggressiveness", type=float, default=0.25, help="Aggressiveness (0.0-1.0)")
    parser.add_argument("--risk_tolerance", type=float, default=0.43, help="Risk tolerance (0.0-1.0)")
    parser.add_argument("--point_to_pool", type=int, default=33, help="Points to pool (int)")
    parser.add_argument("--agent_name", type=str, default=None, help="Optional explicit agent_name. If not provided, name is constructed.")
    parser.add_argument("--print_only", action="store_true", help="Print the constructed agent name and exit (do not connect).")

    args = parser.parse_args()

    # Clamp to sensible ranges
    aggressiveness = 0.25
    risk_tolerance = 0.43
    point_to_pool = 33

    constructed_name = "DoomGuy666"

    print(constructed_name)  # copyable agent name
    if args.print_only:
        logger.info("Printed agent name, exiting due to --print_only.")
    else:
        run_agent(args.host, args.port, constructed_name, args.player_id, aggressiveness, risk_tolerance, point_to_pool)
