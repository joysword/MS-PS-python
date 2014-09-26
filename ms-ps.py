import sys
import os
import re
from itertools import chain
from collections import Counter
import math


def main():

	(data_file, sup_file, out_file) = read_args(sys.argv[1:])

	_file = open(data_file, 'rU')
	txt = _file.read()
	_file.close()

	txt = txt.replace('<{', '').replace('}>', '')
	sequences = txt.split('\n')
	sequences = [seq.split("}{") for seq in sequences if seq]
	sequences = [[[it.strip() for it in item_set.split(',')] for item_set in seq] for seq in sequences]

	# print 'sequences:'
	# print '\n'.join(str(seq) for seq in sequences)
	# raw_input()

	_file = open(sup_file, 'rU')
	txt = _file.read()
	_file.close()

	mis = {match[0]: float(match[1]) for match in re.findall(r'MIS\((\w+)\)\s+=\s+(\d*\.?\d*)', txt)}
	sdc = float(re.search(r'SDC\s=\s(\d*\.?\d*)', txt).group(1))

	# print 'mis:'
	# for k in mis.keys():
	# 	print k, mis.get(k)
	# raw_input()

	# print 'sdc:', sdc
	# raw_input()

	patterns = ms_ps(sequences, mis, sdc)

	write_result(patterns, out_file)


def read_args(args):
	"""Read arguments from commend line."""

	data_file = 'data.txt'
	sup_file = 'para.txt'
	out_file = 'output_new.txt'

	if args:
		if len(args) == 1:
			if args[0] == '-h' or args[0] == '--help':
				_exit('help')
			else:
				_exit('wrong')
		elif len(args) % 2 == 1:
			_exit('wrong')
		else:
			if len(args) >= 2:
				if args[0] != '-d':
					_exit('wrong')
				if not os.path.isfile(args[1]):
					_exit('invalid')
				data_file = args[1]
			if len(args) >= 4:
				if args[2] != '-s':
					_exit('wrong')
				if not os.path.isfile(args[3]):
					_exit('invalid')
				sup_file = args[3]
			if len(args) == 6:
				if args[4] != '-o':
					_exit('wrong')
				if not os.path.isfile(args[5]):
					_exit('invalid')
				out_file = args[5]
			else:
				_exit('wrong')

	return data_file, sup_file, out_file


def _exit(message):
	if message == 'help':
		message = 'usage: -d data_file [-s support_file [-o output_file]]\n'
		message += 'default is data.txt, para.txt and output.txt'
	elif message == 'wrong':
		message = 'wrong arguments, use \'-h\' or \'--help\' to view usage'
	elif message == 'invalid':
		message = 'invalid data file, or support file, or output file'
	print message
	sys.exit(1)


def ms_ps(sequences, mis, sdc):
	if sequences is None or len(sequences) == 0 or mis is None or len(mis) == 0:
		print 'Invalid data sequences or minimum support values'
		return

	patterns = []

	sup_cnt = get_sup_cnt(sequences)
	
	total_sequences = len(sequences)
	
	sup_val = {it: sup_cnt.get(it)/float(total_sequences) for it in sup_cnt.keys()}

	# print 'sup_cnt & sup_val:'
	# for k in sup_cnt.keys():
	# 	print k, sup_cnt.get(k), sup_val.get(k)
	# raw_input()

	# Step 1 & 2, frequent items sorted based on MIS
	freq_items = sorted([it for it in sup_val.keys() if sup_val.get(it) >= mis.get(it)], key=mis.get)

	# print 'frequent items:', freq_items
	# raw_input()

	for it in freq_items:

		# print 'current frequent item:', it
		# raw_input()

		mis_cnt = int(math.ceil(mis.get(it) * total_sequences))

		sequences_with_it = [seq for seq in sequences if has_item(seq, it)]

		# print 'sequences that have \'' + it + '\':'
		# print '\n'.join(str(seq) for seq in sequences_with_it)
		# raw_input()

		sequences_with_it = [filter_sdc(seq, it, sup_val.get(it), sup_val, sdc) for seq in sequences_with_it]

		# print 'sequences that have \'' + it + '\' and filtered using SDC:'
		# for seq in sequences_with_it:
		# 	print seq
		# raw_input()

		patterns += r_prefix_span(it, sequences_with_it, mis_cnt, sup_val, sdc)

		sequences = remove_item(sequences, it)

	return patterns


def get_sup_cnt(_sequences, _it=None):
	flattened = [list(set(chain(*seq))) for seq in _sequences]
	sup_cnt = dict(Counter(it for seq in flattened for it in seq))

	if _it:
		return sup_cnt.get(_it)
	else:
		return sup_cnt


def has_item(l, i):
	if l:
		while isinstance(l[0], list):
			l = list(chain(*l))

		return i in l
	return False


def filter_sdc(_seq, _it, _sup, _sups, _sdc):
	res = []

	if _seq and isinstance(_seq[0], list):
		for l in _seq:
			filtered = filter_sdc(l, _it, _sup, _sups, _sdc)
			if filtered:
				res.append(filtered)
	else:
		for it in _seq:
			if it != _it and abs(_sups.get(it) - _sup) > _sdc:
				continue
			else:
				res.append(it)

	return res


def r_prefix_span(_it, _sequences_with_it, mis_cnt, sup_val, sdc):

	patterns = []
	
	sequences_with_it = remove_infreq_items(_sequences_with_it, mis_cnt)
	freq_items = list(set(chain(*(chain(*sequences_with_it)))))

	# print 'frequent items:', freq_items
	# raw_input()

	len_1_freq_sequences = [[[it]] for it in freq_items]

	_sequences_with_it = remove_infreq_items(_sequences_with_it, mis_cnt)

	# print '_sequences_with_it (now only frequent items):'
	# print '\n'.join(str(seq) for seq in _sequences_with_it)
	# raw_input()

	if has_item(len_1_freq_sequences, _it):
		patterns.append(([[_it]], get_sup_cnt(_sequences_with_it, _it)))

	for seq in len_1_freq_sequences:
		patterns += prefix_span(seq, _sequences_with_it, _it, mis_cnt, sup_val, sdc)

	return patterns


def remove_infreq_items(_sequences, mis_cnt):
	_seqs = [list(set(chain(*seq))) for seq in _sequences]
	cnt = dict(Counter(it for seq in _seqs for it in seq))

	filtered = [[[it for it in item_set if cnt.get(it) >= mis_cnt or it == '_'] for item_set in seq] for seq in _sequences]

	return remove_empty(filtered)


def remove_empty(_list):
	res = []

	if _list and isinstance(_list[0], list):
		for l in _list:
			filtered = remove_empty(l)

			if filtered:
				res.append(filtered)

	else:
		res = _list

	return res


def prefix_span(prefix, _sequences, _it, mis_cnt, sup_val, sdc):
	print 'Prefix:', prefix

	projected_sequences = get_projected_sequences(prefix, _sequences)

	print 'Projected Database:'
	print '\n'.join(str(seq) for seq in projected_sequences)

	tmp_patterns = []
	patterns = []

	if projected_sequences:

		last_set_in_prefix = prefix[-1]
		all_items_same_set = []
		all_items_diff_set = []

		for projected_seq in projected_sequences:
			items_same_set = []
			items_diff_set = []

			for cur_item_set in projected_seq:
				if has_item(cur_item_set, '_'):
					items_same_set += cur_item_set[1:]
				else:
					if contains_in_order(cur_item_set, last_set_in_prefix):
						items_same_set += cur_item_set[cur_item_set.index(last_set_in_prefix[-1]):]

					items_diff_set += cur_item_set

			all_items_same_set += list(set(items_same_set))
			all_items_diff_set += list(set(items_diff_set))

		dict_same_set = dict(Counter(it for it in all_items_same_set))
		dict_diff_set = dict(Counter(it for it in all_items_diff_set))

		for it, sup_cnt in dict_same_set.iteritems():
			if sup_cnt >= mis_cnt:
				patterns.append((prefix[:-1] + [prefix[-1] + [it]], sup_cnt))

		for it, sup_cnt in dict_diff_set.iteritems():
			if sup_cnt >= mis_cnt:
				patterns.append((prefix + [[it]], sup_cnt))

		tmp_patterns = [(pat, sup_cnt) for pat, sup_cnt in tmp_patterns if is_sequence_sdc_satisfied(list(set(chain(*pat))), sup_val, sdc)]

		for (pat, sup_cnt) in tmp_patterns:
			if has_item(pat, _it):
				patterns.append((pat, sup_cnt))
			patterns += prefix_span(pat, _sequences, _it, mis_cnt, sup_val)

	return patterns


def get_projected_sequences(prefix, _sequences):
	projected_sequences = []

	for seq in _sequences:
		cur_pr_item_set = 0
		cur_sq_item_set = 0

		while cur_pr_item_set < len(prefix) and cur_sq_item_set < len(seq):
			if contains_in_order(seq[cur_sq_item_set], prefix[cur_pr_item_set]):
				cur_pr_item_set += 1
				if cur_pr_item_set == len(prefix):
					break

			cur_sq_item_set += 1

		if cur_pr_item_set == len(prefix):
			projected_seq = project(prefix[-1][-1], seq[cur_sq_item_set:])

			if projected_seq:
				projected_sequences.append(projected_seq)

		valid_sequences = remove_empty([[[it for it in item_set if it != '_'] for item_set in seq] for seq in projected_sequences])

		if valid_sequences:
			return remove_empty(projected_sequences)
		else:
			return valid_sequences


def contains_in_order(sq_item_set, pr_item_set):
	if contains(sq_item_set, pr_item_set):
		cur_pr_item = 0
		cur_sq_item = 0

		while cur_pr_item < len(pr_item_set) and cur_sq_item < len(sq_item_set):
			if pr_item_set[cur_pr_item] == sq_item_set[cur_sq_item]:
				cur_pr_item += 1
				if cur_pr_item == len(pr_item_set):
					return True

			cur_sq_item += 1

	return False


def contains(big, small):
	return len(set(big).intersection(set(small))) == len(small)


def project(last_item_in_prefix, suffix):
	first_set_in_suffix = suffix[0]

	if last_item_in_prefix == first_set_in_suffix[-1]:
		return suffix[1:]
	else:
		suffix[0] = ['_'] + first_set_in_suffix[first_set_in_suffix.index(last_item_in_prefix)+1:]
		return suffix


def is_sequence_sdc_satisfied(_list, sup_val, sdc):
	if _list:
		if len(_list) > 1:
			for it1 in _list:
				sup1 = sup_val.get(it1)
				for it2 in _list:
					if it1 != '_' and it2 != '_' and it1 != it2:
						sup2 = sup_val.get(it2)
						if abs(sup1 - sup2) > sdc:
							return False
		return True
	else:
		return False


def remove_item(_list, _it):
	res = []

	if _list and isinstance(_list[0], list):

		for l in _list:
			filtered = remove_item(l, _it)

			if filtered:
				res.append(filtered)

	else:
		res = [it for it in _list if it != _it]

	return res


def write_result(patterns, out_file):
	patterns = sorted(patterns, key=pattern_len)
	result = ''
	
	cur_len = 1

	while True:
		cur_patterns = [pat for pat in patterns if pattern_len(pat) == cur_len]
		if not cur_patterns:
			result += '**end of patterns'
			break

		result += "The number of length " + str(cur_len) + " sequential patterns is " + str(len(cur_patterns)) + '\n'

		for (pat, sup_cnt) in cur_patterns:
			result += 'Pattern: <{'
			result += '}{'.join(','.join(item_set) for item_set in pat)
			result += '}> Count: ' + str(sup_cnt) + '\n'

		cur_len += 1

		result += '\n'

	print result

	_file = open(out_file, 'w')
	_file.write(result)
	_file.close()


def pattern_len(pat):

	l = pat[0]

	while isinstance(l[0], list):
		l = list(chain(*l))

	return len(l)

if __name__ == '__main__':
	main()