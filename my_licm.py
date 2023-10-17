import json
import sys
import copy
from random import randint

def get_basic_blocks(_code):
	"""
	Returns a dictionary of blocks, separated by the function name.
	Each block is a dictionary itself, with keys "instrs" and "successors".
	The "succesors" key will be used when constructing the cfg.
	"""
	blocks = dict()
	for func in _code["functions"]:
		blocks[func["name"]] = {}
		new_block = {"instrs": [], "predecessors": [], "successors": [], "dominators": []}
		fun_len = len(func["instrs"]) - 1
		unnamed_blocks_cntr = 0
		cur_label = ""
		for instr_idx, instr in enumerate(func["instrs"]):
			if "label" in instr:
				if not new_block["instrs"] == []:
					to_append = new_block.copy()
					if cur_label == "":
						### Name the entry block as "entry", not "b0". If not the entry,
						### use the convention and name it bn for the right n.
						if unnamed_blocks_cntr == 0:
							cur_label = "entry"
						else:
							cur_label = "b" + str(unnamed_blocks_cntr)
							unnamed_blocks_cntr += 1
					blocks[func["name"]][cur_label] = to_append
				new_block = {"instrs": [], "predecessors": [], "successors": [], "dominators": []}
				new_block["instrs"] = [instr]
				cur_label = instr["label"]
				continue
			new_block["instrs"].append(instr)
			if is_breaking_block(instr):
				#print(f"instr is breaking block. {instr}")
				#print(f"new block is {new_block}")
				if cur_label == "":
					### Name the entry block as "entry", not "b0". If not the entry,
					### use the convention and name it bn for the right n.
					if unnamed_blocks_cntr == 0:
						cur_label = "entry"
					else:
						cur_label = "b" + str(unnamed_blocks_cntr)
						unnamed_blocks_cntr += 1
				to_append2 = new_block.copy()
				blocks[func["name"]][cur_label] = to_append2
				new_block = {"instrs": [], "predecessors": [], "successors": [], "dominators": []}
				continue
			if instr_idx == fun_len:
				if cur_label == "":
					### Name the entry block as "entry", not "b0". If not the entry,
					### use the convention and name it bn for the right n.
					if unnamed_blocks_cntr == 0:
						cur_label = "entry"
					else:
						cur_label = "b" + str(unnamed_blocks_cntr)
						unnamed_blocks_cntr += 1
				to_append3 = new_block.copy()
				blocks[func["name"]][cur_label] = to_append3
				new_block = {"instrs": [], "predecessors": [], "successors": [], "dominators": []}
				continue
		if not new_block["instrs"] == []:
			to_append4 = new_block.copy()
			blocks[func["name"]][cur_label] = to_append4
	return blocks

def is_breaking_block(_instr):
	is_breaking = False
	##TODO: check whether ret should be here or not! or _instr["op"] == "ret"
	if _instr["op"] == "jmp" or _instr["op"] == "br":
		is_breaking = True
	return is_breaking

def get_cfg(_blocks):
    for _, func in enumerate(_blocks):
        for block_idx, block in enumerate(_blocks[func]):
            #print(block)
            if "op" in _blocks[func][block]["instrs"][-1]:
                if _blocks[func][block]["instrs"][-1]["op"] == "jmp" or _blocks[func][block]["instrs"][-1]["op"] == "br":
                    _blocks[func][block]["successors"] = _blocks[func][block]["instrs"][-1]["labels"]
                    for label in _blocks[func][block]["instrs"][-1]["labels"]:
                        _blocks[func][label]["predecessors"].append(block)
                else:
                    if (not _blocks[func][block]["instrs"][-1]["op"] == "ret") and (block_idx < len(_blocks[func]) - 1):
                        temp = list(_blocks[func].keys())
                        _blocks[func][block]["successors"].append(temp[block_idx + 1])
                        _blocks[func][temp[block_idx + 1]]["predecessors"].append(block)
            elif ("label" in _blocks[func][block]["instrs"][-1]) and (block_idx < len(_blocks[func]) - 1):
                temp = list(_blocks[func].keys())
                _blocks[func][block]["successors"].append(temp[block_idx + 1])
                _blocks[func][temp[block_idx + 1]]["predecessors"].append(block)
    return _blocks

def print_cfg(_cfg):
	for func in _cfg:
		for block in _cfg[func]:
			print(block)
			print(_cfg[func][block]["predecessors"])
			print(_cfg[func][block]["successors"])

def compute_reaching_defs(_cfg, _inputs):
	in_defs = dict()
	out_defs = dict()
	for func_idx, func in enumerate(_cfg):
		in_defs[func] = dict()
		out_defs[func] = dict()
		worklist = list(_cfg[func].keys())
		for block_idx, block in enumerate(worklist):
			if block_idx == 0:
				in_defs[func][block] = _inputs[func]
				out_defs[func][block] = []
			else:
				in_defs[func][block] = []
				out_defs[func][block] = []
		while not worklist == []:
			block = worklist[randint(0, len(worklist) - 1)]
			in_defs[func][block] = df_merge(out_defs[func], _cfg[func][block])
			#print(f"The new in_defs for block {block} is {in_defs[func][block]}")
			new_out = df_transfer(in_defs[func][block], _cfg[func][block], block)
			if not new_out == out_defs[func][block]:
				for successor in _cfg[func][block]["successors"]:
					if not successor in worklist:
						worklist.append(successor)
			else:
				pass
			worklist.remove(block)
			out_defs[func][block] = new_out
	return in_defs, out_defs

def df_merge(_out_defs, _block):
	defs = []
	for block in _block["predecessors"]:
		#print(f"block is {block} - union between {defs} and {_out_defs[block]}")
		defs = union(defs, _out_defs[block])
	return defs

def union(a, b):
	dset = set()
	for instr in a:
		dset.add(json.dumps(instr, sort_keys=True))
	for instr in b:
		dset.add(json.dumps(instr, sort_keys=True))
	res = []
	for elem in list(dset):
		res.append(json.loads(elem))
	return res

def df_transfer(_defs, _block, _block_name):
	def_vars = []
	def_instrs = dict()
	#### Initialize with the input definitions.
	for definition in _defs:
		if not definition["dest"] in def_vars:
			def_vars.append(definition["dest"])
		if not definition["dest"] in def_instrs:
			def_instrs[definition["dest"]] = [definition]
		else:
			#print(f"Appending!! {definition}")
			#print(def_instrs[definition["dest"]])
			def_instrs[definition["dest"]].append(definition)

	#### Bring in the definitions within the block.
	for instr_idx, instr in enumerate(_block["instrs"]):
		if "dest" in instr:
			if not instr["dest"] in def_vars:
				def_vars.append(instr["dest"])
			new_instr = copy.deepcopy(instr)
			new_instr["block"] = _block_name
			new_instr["index"] = instr_idx
			def_instrs[instr["dest"]] = [new_instr]
	
	instrs = []
	for elem in list(def_instrs.values()):
		instrs = instrs + elem
				
	return instrs

def get_inputs(_code):
	inputs = dict()
	for _, func in enumerate(_code["functions"]):
		inputs[func["name"]] = []
		if "args" in func:
			for arg in func["args"]:
				inputs[func["name"]].append({"is_input": True, "dest": arg["name"]})
	return inputs

def get_dominators(_cfg):
    dominators = dict()
    dominatees = dict()
    for _, func in enumerate(_cfg):
        ### Initialize the dominators set.
        dominators[func] = dict()
        dominatees[func] = dict()
        block_names = list(_cfg[func].keys())
        for name in block_names:
            if name == block_names[0]:
                dominators[func][name] = [block_names[0]]
                dominatees[func][name] = [block_names[0]]
            else:
                dominators[func][name] = block_names
                dominatees[func][name] = []

        has_changed = True
        while has_changed:
            #print("going again")
            has_changed = False
            for _, block in enumerate(dominators[func]):
                if block == block_names[0]:
                    continue
                res = intersection(block, _cfg[func][block]["predecessors"], dominators[func])
                #print(f"block is {block}, res is {res}, doms are {dominators[func][block]}")
                if not res == dominators[func][block]:
                    has_changed = True
                dominators[func][block] = res
        for _, block in enumerate(dominators[func]):
            for dom in dominators[func][block]:
                #print(f"dom is {dom}, block is {block}, res is {res}")
                dominatees[func][dom].append(block)
    return dominators, dominatees



def intersection(_block, _preds, _dominators):
	res = list(_dominators.keys())
	for pred in _preds:
		res = list(set(_dominators[pred]) & set(res))
	if not _block in res:
		res.append(_block)
	return res

def get_natural_loops(_cfg, _dominators):
	loops = dict()
	for _, func in enumerate(_cfg):
		loops[func] = []
		for _, block in enumerate(_cfg[func]):
			for succ in _cfg[func][block]["successors"]:
				if succ in _dominators[func][block]:
					loops[func].append({"header": succ, "latch": block, "preheader": "", "body": [], "exiting": [], "invariants": {}})
					if succ == block:
						#print(f"succ = block")
						#reached = loop_dfs(_cfg[func], [succ], succ, block)
						reached = [block]
					else:
						#print(f"succ != block")
						reached = loop_dfs(_cfg[func], [succ, block], succ, block)
					#print(f"reached is {reached}")
					for elm in reached:
						if not succ in _dominators[func][elm]:
							reached.remove(elm)
						for pred in _cfg[func][elm]["predecessors"]:
							if not pred in reached and succ in _dominators[func][pred]:
								reached.append(pred)
					loops[func][-1]["body"] = reached
					for elm in loops[func][-1]["body"]:
						for elm_succ in _cfg[func][elm]["successors"]:
							if not elm_succ in loops[func][-1]["body"]:
								if not elm in loops[func][-1]["exiting"]:
									loops[func][-1]["exiting"].append(elm)
	return loops

def loop_dfs(_cfg, _reached, _goal, _curr):
	#print(f"Inside dfs. reached is {_reached}")
	for block in _cfg[_curr]["predecessors"]:
		if block == _goal:
			return _reached
		else:
			_reached.append(block)
			return loop_dfs(_cfg, _reached, _goal, block)

def add_preheader(_cfg, _loops):
	for _, func in enumerate(_loops):
		cntr = 0
		headers = []
		pre_headers = dict()
		for elm_idx, elm in enumerate(_loops[func]):
			if not elm["header"] in headers:
				headers.append(elm["header"])
			else:
				_loops[func][elm_idx]["preheader"] = pre_headers[elm["header"]]
				continue
			header = elm["header"]
			pre_name = "preheader.Ali." + str(cntr)
			pre_headers[header] = pre_name
			cntr += 1
			_loops[func][elm_idx]["preheader"] = pre_name
            #print(f"header is {header}, prename is {pre_name}")
			_cfg[func][pre_name] = {"instrs": [{"label": pre_name}], "predecessors": [], "successors": [header], "dominators": []}
			_cfg[func][header]["predecessors"].append(pre_name)
			for pred in _cfg[func][header]["predecessors"]:
				if pred in elm["body"] or pred == pre_name:
					continue
				_cfg[func][pre_name]["predecessors"].append(pred)
				_cfg[func][pred]["successors"].remove(header)
				_cfg[func][pred]["successors"].append(pre_name)
				_cfg[func][header]["predecessors"].remove(pred)
				if "op" in _cfg[func][pred]["instrs"][-1]:
					if _cfg[func][pred]["instrs"][-1]["op"] == "jmp" or _cfg[func][pred]["instrs"][-1]["op"] == "br":
						for lab_idx, lab in enumerate(_cfg[func][pred]["instrs"][-1]["labels"]):
							if lab == header:
								_cfg[func][pred]["instrs"][-1]["labels"][lab_idx] = pre_name
	return _cfg, _loops

def get_loop_invariants(_loops, _defs, _cfg):
	for _, func in enumerate(_loops):
		for loop_idx, loop in enumerate(_loops[func]):
			for block in loop["body"]:
				_loops[func][loop_idx]["invariants"][block] = [0] * len(_cfg[func][block]["instrs"])
		for loop_idx, loop in enumerate(_loops[func]):
			has_changed = True
			#print(f"Inside the loop for - loops is {_loops}")
			while has_changed:
				has_changed = False            
				for block in loop["body"]:
					for instr_idx, instr in enumerate(_cfg[func][block]["instrs"]):
						#pre = loop["preheader"]
						#he = loop["header"]
						#print(f"loop pre is {pre}, header is {he}, block is {block}, idx is {instr_idx}")
						if "op" in instr:
							if instr["op"] == "br":
								continue
						if "args" in instr:
							is_invariant = True
							for arg in instr["args"]:
								if not check_invariance(arg, instr_idx, _defs[func][block], _cfg[func][block], loop, block):
									#print("Not invariant!")
									is_invariant = False
							if is_invariant:
								#print("Is invariant!")
								if not _loops[func][loop_idx]["invariants"][block][instr_idx] == 1:
									_loops[func][loop_idx]["invariants"][block][instr_idx] = 1
									has_changed = True
	return _loops

def check_invariance(_arg, _idx, _defs, _block, _loop, _block_name):
	for i in reversed(range(_idx)):
		if "dest" in _block["instrs"][i]:
			if _block["instrs"][i]["dest"] == _arg:
				if _loop["invariants"][_block_name][i] == 0:
					return False
				else:
					#lat = _loop["latch"]
					#print(f"arg is {_arg}, block is {_block_name}, index is {_idx}, latch is {lat} - All args have been marked LI.")
					return True

	reach_cntr = 0
	for instr in _defs:
		if instr["dest"] == _arg:
			#print(f"instr is {instr}")
			if instr["block"] in _loop["body"]:
				reach_cntr += 1
				#print(f"reach counter is {reach_cntr}")
				if reach_cntr > 1:
					return False
				if _loop["invariants"][instr["block"]][instr["index"]] == 0:
					return False
	#lat = _loop["latch"]
	#print(f"arg is {_arg}, block is {_block_name}, index is {_idx}, latch is {lat} - Conditions were met.")
	return True

def move_invariants(_cfg, _loops, _dominators):
	for _, func in enumerate(_loops):
		to_delete = []
		
		for loop_idx, loop in enumerate(_loops[func]):
			to_delete.append({})
			
			defs, uses = get_loop_defs_n_uses(loop["body"], _cfg[func])
			for block in loop["body"]:
				#to_delete = []
				to_delete[loop_idx][block] = []
				
				for instr_idx, instr in enumerate(_cfg[func][block]["instrs"]):
					if loop["invariants"][block][instr_idx] == 0:
						continue
					if not "dest" in instr:
						continue
					if "dest" in instr:
						dominates_all_uses = True
						if instr["dest"] in uses:
							for use in uses[instr["dest"]]:
								if not block in _dominators[func][use["block"]]:
									dominates_all_uses = False
						if not dominates_all_uses:
							continue
						if len(defs[instr["dest"]]) > 1:
							continue
						for exit in loop["exiting"]:
							if not block in _dominators[func][exit]:
								continue
					_cfg[func][loop["preheader"]]["instrs"].append(_cfg[func][block]["instrs"][instr_idx])
					
					to_delete[loop_idx][block].append(instr_idx)
					#to_delete.append(instr_idx)
				#for idx in sorted(to_delete, reverse=True):
				#	del _cfg[func][block]["instrs"][idx]
		has_been_deleted = dict()
		for block in _cfg[func]:
			has_been_deleted[block] = [0] * len(_cfg[func][block]["instrs"])
		for loop_idx, loop in enumerate(_loops[func]):
			for block in loop["body"]:
				for idx in sorted(to_delete[loop_idx][block], reverse=True):
					if has_been_deleted[block][idx] == 0:
						del _cfg[func][block]["instrs"][idx]
						has_been_deleted[block][idx] = 1
	return _cfg

def get_loop_defs_n_uses(_blocks, _cfg):
	defs = dict()
	uses = dict()
	for block in _blocks:
		for instr in _cfg[block]["instrs"]:
			if "dest" in instr:
				if not instr["dest"] in defs:
					defs[instr["dest"]] = [{"instr": instr, "block": block}]
				else:
					defs[instr["dest"]].append({"instr": instr, "block": block})
			if "args" in instr:
				for arg in instr["args"]:
					if not arg in uses:
						uses[arg] = [{"instr": instr, "block": block}]
					else:
						uses[arg].append({"instr": instr, "block": block})
	return defs, uses

def erase_metadata(_cfg, _code, _headers):
	for _, func in enumerate(_cfg):
		heads = list(_headers[func].keys())
		preheaders = list(_headers[func].values())
		preheader_added = dict()
		for head in heads:
			if not head in preheader_added:
				preheader_added[head] = False
		for old_func_idx, old_func in enumerate(_code["functions"]):
			if old_func["name"] == func:
				#print(f"Erasing - func is {func}")
				_code["functions"][old_func_idx]["instrs"] = []
				for _, block in enumerate(_cfg[func]):
					if not block in heads and not block in preheaders:
						new_instrs = _cfg[func][block]["instrs"]
						#print(f"new instructions are {new_instrs}")
						#print(f"Normal - writing block {block}, func is {func}")
						_code["functions"][old_func_idx]["instrs"] = _code["functions"][old_func_idx]["instrs"] + _cfg[func][block]["instrs"]
					elif block in preheaders:
						continue
					else:
						if not preheader_added[block]:
							new_instrs = _cfg[func][_headers[func][block]]["instrs"]
							#print(f"new instructions are {new_instrs}")
							#print(f"Preheader - writing block {_headers[func][block]}, func is {func}")
							_code["functions"][old_func_idx]["instrs"] = _code["functions"][old_func_idx]["instrs"] + _cfg[func][_headers[func][block]]["instrs"]
							preheader_added[block] = True
						new_instrs = _cfg[func][block]["instrs"]
						#print(f"new instructions are {new_instrs}")
						#print(f"Header - writing block {block}, func is {func}")
						_code["functions"][old_func_idx]["instrs"] = _code["functions"][old_func_idx]["instrs"] + _cfg[func][block]["instrs"]

	return _code
                        
if __name__ == "__main__":
	code = json.load(sys.stdin)
	blocks = get_basic_blocks(code)
	#print(f"basic blocks are {blocks}")
	cfg = get_cfg(blocks)
	#print(f"Initial cfg is {cfg}")
	inputs = get_inputs(code)
	#print(inputs)
	in_defs, out_defs = compute_reaching_defs(cfg, inputs)
	#print(in_defs["main"]["loop.bound"])
	dominators, dominatees = get_dominators(cfg)
	natural_loops = get_natural_loops(cfg, dominators)
	#print(f"loops are {natural_loops}")
	cfg, natural_loops = add_preheader(cfg, natural_loops)
	#print_cfg(cfg)
	natural_loops = get_loop_invariants(natural_loops, in_defs, cfg)
	#print("Natural loops with invariants:")
	#print(natural_loops)
	cfg = move_invariants(cfg, natural_loops, dominators)
	#print(cfg)
	headers = dict()
	for func in natural_loops:
		headers[func] = dict()
		for loop in natural_loops[func]:
			if not loop["header"] in headers[func]:
				headers[func][loop["header"]] = loop["preheader"]

	#print(cfg)
	#print(f"headers is {headers}")
	res = erase_metadata(cfg, code, headers)
	
	json.dump(res, sys.stdout, indent=2, sort_keys=True)