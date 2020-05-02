## cases
# is there an else?
	# yes
		# does the else assign
			# yes
				# does the else return
					# yes
						# does the if assign
							# yes
								# does the if return
									# yes
										no phi needed
									# no
										phi [recent ir, recent block], [if ir, if block]
							# no
								no phi needed
					# no
						# does the if assign
							# yes
								# does the if return
									# yes
										no phi needed
									# no
										phi [if ir, if block], [else ir, else block]
							# no
								phi [recent ir, recent block], [else ir, else block]
			# no
				# does the if return
					# yes
						no phi needed
					# no
					phi [recent ir, recent block], [if ir, if block]

	# no
		# does the if return
			# yes
				no phi needed
			# no
				phi [recent ir, recent block], [if ir, if block]

## instead of ^ this spaghetti code:
keep track of basic blocks predecessors

## do we even need a phi with only one branch?
can we get rid of this code and similar:
phi_code = "%{} = phi {} [%{}, %{}]".format(
                                self.reg_num,
                                ste.node.type,
                                first_ir_name, first_branch_name,
                            )

i think we don't