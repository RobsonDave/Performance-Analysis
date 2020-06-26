
# Produce a csv file with:
#	column A: seconds since top of the hour
#		from log entry timestamp
#		minutes*60 + seconds + hundredths of a second (two decimal places)
#	column B: seconds since base time
#		base time is in first row - B1
#		base time is initially set to zero by this script
#		later reset to start of analysis period
#		the contents of this column are formulas
#	column C: error flag
#	column D: body (description of log event)

import re

# Patterns for "extraneous" information (to be stripped out)
meta_info_pattern = re.compile(r"\[[\d;]*m")
INFO_pattern1 = re.compile(r"\[\s*INFO\s*\]")
INFO_pattern2 = re.compile(r"INFO")
WARN_pattern = re.compile(r"\[\s*WARN\s*\]")
ERROR_pattern = re.compile(r"\[\s*ERROR\s*\]")

# Patterns for two types of timestamp
# 1: date | 2: hour | 3: minute | 4: second | 5: second fraction | 6: body
time_stamp_pattern1 = re.compile(r"\s\[(\d{4}-\d{2}-\d{2})\s(\d{2}):(\d{2}):(\d{2})\.(\d{6}|\d{9})\]\s(.*)")
# 1: date | 2: hour | 3: minute | 4: second | 5: body
time_stamp_pattern2 = re.compile(r"\[(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})-\d{2}:\d{2}\]\s(.*)")

def process_reactor_log(input_file_name, output_file_name):
	input_file = open(input_file_name, "r")
	output_file = open(output_file_name, "w")
	# footnotes are lines in the log that don't have timestamps
	# they are moved to the end of the output file for readability
	# a reference to the footnote number appears in the output file where the original information was
	# footnote_index is the number of the current/last footnote
	footnote_index = 0
	between_footnotes = True
	# footnote_lines are the actual footnotes, gathered to be put at the end
	footnote_rows = []
	# row_number is the index of the next output row to be written
	# it is used to create the formulas in column B
	row_number = 1
	output_file.write("Seconds,Seconds since,Error,Body,Notes\n")
	row_number = row_number + 1
	output_file.write(",0,,\n")
	row_number = row_number + 1
	for line in input_file:
		# Remove escapes, weird fluff, and labels; remember errors
		stripped_line = line.replace("\x1b", "")
		stripped_line = stripped_line.replace(",", ";")
		stripped_line = meta_info_pattern.sub("",stripped_line)
		stripped_line = INFO_pattern1.sub("",stripped_line)
		stripped_line = INFO_pattern2.sub("",stripped_line)
		stripped_line = WARN_pattern.sub("",stripped_line)
		if ERROR_pattern.match(stripped_line):
			# error_flag remembers to put an E in the error column
			error_flag = "E"
			stripped_line = ERROR_pattern.sub("",stripped_line)
		else:
			error_flag = ""
		# At this point the timestamp should be at the beginning
		time_stamp_match1 = time_stamp_pattern1.match(stripped_line)
		time_stamp_match2 = time_stamp_pattern2.match(stripped_line)
		if time_stamp_match1:
			# The line is a normal timestamped entry
			between_footnotes = True #We are not gathering up a footnote
			minutes = float(time_stamp_match1.group(3))
			seconds = float(time_stamp_match1.group(4))
			fraction = float(time_stamp_match1.group(5)[0:2])/100
			time = str((minutes*60)+seconds+fraction)
			body = time_stamp_match1.group(6)
			row = time+",=A"+str(row_number)+"-B2,"+error_flag+","+body+",---,\n"
		elif time_stamp_match2:
			# The line is an alternate timestamped entry
			between_footnotes = True #We are not gathering up a footnote
			minutes = float(time_stamp_match2.group(3))
			seconds = float(time_stamp_match2.group(4))
			time = str((minutes*60)+seconds)
			body = time_stamp_match2.group(5)
			row = time+",=A"+str(row_number)+"-B2,"+error_flag+","+body+",---,\n"
		else:
			# The line has no timestamp, so it is part of a footnote
			if between_footnotes:
				# Start a new footnote
				between_footnotes = False
				footnote_index = footnote_index + 1
				footnote_ref = "<<Footnote "+str(footnote_index)+">>\n"
				footnote_rows.append(footnote_ref)
				footnote_rows.append(stripped_line)
				# The row for the main text is just the footnote reference
				row = ",,,"+footnote_ref
			else:
				# Add a line to the current footnote
				footnote_rows.append(stripped_line)
				# There is no line to add to the main text
				row = False
		if row:
			output_file.write(row)
			row_number = row_number + 1
	#The main text is complete. Now just add the footnotes that have been accumulated
	for footnote in footnote_rows:
		row = ",,,"+footnote
		output_file.write(row)
	output_file.close
	input_file.close
