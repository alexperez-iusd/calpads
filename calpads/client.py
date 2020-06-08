import requests
import logging
import json
import re
import time
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl, urljoin
from collections import deque
from lxml import etree
from .reports_form import ReportsForm, REPORTS_DL_FORMAT
from .extracts_form import ExtractsForm
from .files_upload_form import FilesUploadForm


class CALPADSClient:

    def __init__(self, username, password):
        self.host = "https://www.calpads.org/"
        self.username = username
        self.password = password
        self.credentials = {'Username': self.username,
                            'Password': self.password}
        self.visit_history = deque(maxlen=10)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"})
        self.session.hooks['response'].append(self._handle_event_hooks)
        self.log = logging.getLogger(__name__)
        log_fmt = f'%(levelname)s: %(asctime)s {self.__class__.__name__}.%(funcName)s: %(message)s'
        stream_hdlr = logging.StreamHandler()
        stream_hdlr.setFormatter(logging.Formatter(fmt=log_fmt))
        self.log.addHandler(stream_hdlr)
        try:
            self.__connection_status = self._login()
        except RecursionError:
            self.log.info("Looks like the provided credentials might be incorrect. Confirm credentials.")

    def _login(self):
        """Login method which generally doesn't need to be called except when initializing the client."""
        #Dance the OAuth Dance
        self.session.get(self.host)
        # self.log.debug(homepage_response.url)
        # self.log.debug(self.session.cookies)
        # self.log.debug(self.session.get(self.host + 'Leas?format=JSON').content) # Easy check if logging in happened
        return self.visit_history[-1].status_code == 200 and self.visit_history[-1].url == self.host

    @property
    def is_connected(self):
        """User exposed attribute to check whether the client successfully connected. Might return false positives."""
        return self.__connection_status #Unclear, but there is a chance this returns a false positive

    def get_leas(self):
        """Returns the list of LEAs provided by CALPADS
        Returns:
            list of LEA dictionaries with the keys Disabled, Group, Selected, Text, Value
        """
        response = self.session.get(urljoin(self.host, 'Leas?format=JSON'))
        return json.loads(response.content)

    def get_all_schools(self, lea_code):
        """Returns the list of schools for the provided lea_code

        Args:
            lea_code (str): string of the seven digit number found next to your LEA name in the org select menu. For most LEAs,
                this is the CD part of the County-District-School (CDS) code. For independently reporting charters, it's the S.

        Returns:
            list of School dictionaries with the keys Disabled, Group, Selected, Text, Value
        """
        response = self.session.get(urljoin(self.host, f"/SchoolListingAll?lea={lea_code}&format=JSON"))
        return json.loads(response.content)

    def get_homepage_important_messages(self):
        """Returns the CALPADS' Homepage Important Messages section in JSON
        Returns:
            a dict with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, '/HomepageImportantMessages?format=JSON'))
        return json.loads(response.content)

    def get_homepage_anomaly_status(self):
        """Returns the CALPADS' Homepage Anomaly Status section in JSON format
        Returns:
            a dict with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, '/HomepageAnomalyStatus?format=JSON'))
        return json.loads(response.content)

    def get_homepage_certification_status(self):
        """Returns the CALPADS' Homepage Certification Status section in JSON format
        Returns:
            a dict with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, '/HomepageCertificationStatus?format=JSON'))
        return json.loads(response.content)

    def get_homepage_submission_status(self):
        """Returns the CALPADS' Homepage Submission Status section in JSON format
        Returns:
            a dict with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, '/HomepageSubmissions?format=JSON'))
        return json.loads(response.content)

    def get_homepage_extract_status(self):
        """Returns the CALPADS' Homepage Extract Status section in JSON format
        Returns:
            a dict with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, '/HomepageNotifications?format=JSON'))
        return json.loads(response.content)

    def get_enrollment_history(self, ssid):
        """Returns a JSON object with the Enrollment history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/Enrollment?format=JSON'))
        return json.loads(response.content)

    def get_demographics_history(self, ssid):
        """Returns a JSON object with the Demographics history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/Demographics?format=JSON'))
        return json.loads(response.content)

    def get_address_history(self, ssid):
        """Returns a JSON object with the Address history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/Address?format=JSON'))
        return json.loads(response.content)

    def get_elas_history(self, ssid):
        """Returns a JSON object with the English Language Acquisition Status (ELAS) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/EnglishLanguageAcquisition?format=JSON'))
        return json.loads(response.content)

    def get_program_history(self, ssid):
        """Returns a JSON object with the Program history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/Program?format=JSON'))
        return json.loads(response.content)

    def get_student_course_section_history(self, ssid):
        """Returns a JSON object with the Student Course Section history (SCSE, SCSC) for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/StudentCourseSection?format=JSON'))
        return json.loads(response.content)

    def get_cte_history(self, ssid):
        """Returns a JSON object with the Career Technical Education (CTE) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/CareerTechnicalEducation?format=JSON'))
        return json.loads(response.content)

    def get_stas_history(self, ssid):
        """Returns a JSON object with the Student Absence Summary (STAS) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/StudentAbsenceSummary?format=JSON'))
        return json.loads(response.content)

    def get_sirs_history(self, ssid):
        """Returns a JSON object with the Student Incident Result (SIRS) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/StudentIncidentResult?format=JSON'))
        return json.loads(response.content)

    def get_soff_history(self, ssid):
        """Returns a JSON object with the Student Offense (SOFF) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/Offense?format=JSON'))
        return json.loads(response.content)

    def get_assessment_history(self, ssid):
        """Returns a JSON object with the Student Offense (SOFF) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/Assessment?format=JSON'))
        return json.loads(response.content)

    def get_sped_history(self, ssid):
        """Returns a JSON object with the Special Education (SPED) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/SPED?format=JSON'))
        return json.loads(response.content)

    def get_ssrv_history(self, ssid):
        """Returns a JSON object with the Student Services (SSRV) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/SSRV?format=JSON'))
        return json.loads(response.content)

    def get_psts_history(self, ssid):
        """Returns a JSON object with the Postsecondary Transition Status (PSTS) history for the provided SSID

        Args:
            ssid (int, str): the 10 digit CALPADS Statewide Student Identifier

        Returns:
            a JSON object with a Data key and a total record count key (the name of this key can vary).
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Student/{ssid}/PSTS?format=JSON'))
        return json.loads(response.content)

    def get_requested_extracts(self, lea_code):
        """Returns a JSON object with the Postsecondary Transition Status (PSTS) history for the provided SSID

        Args:
            lea_code (str): string of the seven digit number found next to your LEA name in the org select menu. For most LEAs,
                this is the CD part of the County-District-School (CDS) code. For independently reporting charters, it's the S.

        Returns:
            a JSON object with a Data key
            Expected data is under Data as a List where each item is a "row" of data
        """
        response = self.session.get(urljoin(self.host, f'/Extract?SelectedLEA={lea_code}&format=JSON'))
        return json.loads(response.content)

    def download_report(self, lea_code, report_code, file_name=None, is_snapshot=False,
                        download_format='CSV', form_data=None, dry_run=False):
        """Download CALPADS ODS or Snapshot Reports

        Args:
            lea_code (str): string of the seven digit number found next to your LEA name in the org select menu. For most LEAs,
                this is the CD part of the County-District-School (CDS) code. For independently reporting charters, it's the S.
            report_code (str): Currently supports all known reports. Expected format is a string e.g. '8.1', '1.17', and '1.18'.
                For reports that have letters in them, for example the 8.1 EOY3, expected input is '8.1eoy3' OR '8.1EOY3'.
                No spaces, all one word.
            file_name (str): the name of the file to pass to open(file_name, 'wb'). Assumes any subdirectories
                parent directories referenced in the file name already exist.
            is_snapshot (bool): when True downloads the Snapshot Report. When False, downloads the ODS Report.
            download_format (str): The format in which you want the download for the report.
                Currently supports: csv, excel, pdf, word, powerpoint, tiff, mhtml, xml, datafeed
            form_data (dict): the data that should be sent with the form request. Usually, all select fields for the
                form need to be provided. To see list of valid values, set dry_run=True.
            dry_run (bool): when False, it downloads the report. When True, it doesn't download the report and instead
                returns a dict with the form fields and their expected inputs.

        Returns:
            bool: True for a successful download of report, else False.
            dict: when dry_run=True, it returns a dict of the form fields and their expected inputs for report manipulation

        """
        if not REPORTS_DL_FORMAT.get(download_format.upper()):
            self.log.info('{} is not a supported reports download format. Try: {}'
                          .format(download_format, ' '.join(REPORTS_DL_FORMAT.keys())))
            raise Exception('Bad download format')
        if not file_name:
            file_name = 'data'
        with self.session as session:
            self._select_lea(lea_code)
            report_url = self._get_report_link(report_code.lower(), is_snapshot)
            if report_url:
                session.get(report_url)
            else:
                raise Exception("Report Not Found")
            report_page_root = etree.fromstring(self.visit_history[-1].text, parser=etree.HTMLParser(encoding='utf8'))
            iframe_url = report_page_root.xpath("//iframe[@src and not(contains(@src, 'KeepAlive'))]")[0].attrib['src']
            #self.log.debug(iframe_url)
            session.get(iframe_url)
            form = ReportsForm(self.visit_history[-1].text)
            if dry_run:
                return form.filtered_parse

            if form_data:
                formatted_form_data = form.get_final_form_data(form_data)
            else:
                self.log.warning("Most report forms require at least some input, especially for Select form fields.")
                formatted_form_data = form.get_final_form_data(dict())

            # TODO: Test how form data treats None or False diferently from empty string
            submitted_form_data = {k: v for k, v in formatted_form_data.items() if v != ''}

            #self.log.debug('The form data about to be submitted: \n{}\n'.format(submitted_form_data))
            #self.log.debug('These are the data keys about to be submitted: \n{}\n'.format(submitted_form_data.keys()))
            #TODO: Document that it seems like at a minimum all "select" fields need to have values provided for
            #Alternatively, provide default values
            session.post(self.visit_history[-1].url, data=submitted_form_data)

            # Regex for grabbing the base, direct download URL for the report
            regex = re.compile('(?<="ExportUrlBase":")[^"]+(?=")')  # Look for text sandwiched between the lookbehind and
            # the lookahead, but EXCLUDE the double quotes (i.e. find the first double quotes as the upper limit of the text)

            split_query = None
            if regex.search(self.visit_history[-1].text):
                self.log.debug('Found ExportUrlBase in the URL')
                export_url_base = regex.search(self.visit_history[-1].text).group(0)
                scheme, netloc, path, query, frag = urlsplit(urljoin("https://reports.calpads.org",
                                                                     export_url_base)
                                                             .replace('\\u0026', '&')
                                                             .replace('%3a', ':')
                                                             .replace('%2f', '/'))
                split_query = parse_qsl(query)

            if split_query:
                self.log.debug("Adding Format parameter to the URL")
                split_query.append(('Format', REPORTS_DL_FORMAT[download_format.upper()]))
                self.log.debug("Rejoining the query elements again")
                report_dl_url = urlunsplit([scheme, netloc, path, urlencode(split_query), frag])
                session.get(report_dl_url)
                # Cautionary Tale here if the content is compressed:
                # https://stackoverflow.com/a/50825553
                # Might need to revisit later
                with open(file_name, 'wb') as f:
                    f.write(self.visit_history[-1].content)
                    return True

            #If you made it this far, something went wrong.
            return False

    def request_extract(self, lea_code, extract_name, form_data=None, by_date_range=False,
                        by_as_of_date=False, dry_run=False):
        """
        Request an extract with the extract_name from CALPADS.

        For Direct Certification Extract, pass in extract_name='DirectCertification'.
        For DSEA Extract, pass in extract_name='DSEAExtract'
        For the others, use their abbreviated acronym, e.g. SENR, SELA, etc.

        When dry_run is true, this returns a dict with suggestions for form_data inputs. The keys are the keys,
        the values are options for valid values. If the value is str, then any string is allowed. Date parameters
        will provide a value with formatting instructions (namely, MM/DD/YYYY). Select fields have dict values in
        the form of: {'FieldName': {'_allows_multiple': True, 'val1': 'internal_val'}. The expected input should
        look like form_data = [('FieldName', 'internal_val')], that is take the key of dict, and the value of the
        nested dict. 'val1' is the value dispalyed in the UI. If '_allows_multiple' is False, then only one of those
        field keys should be sent in the request. If '_allows_multiple' is True, then the key can have multiple values.
        A common example is schools: [('School', '0000001'), ('School', '0000002')] for NPS and Private schools.

        Args:
            lea_code (str): string of the seven digit number found next to your LEA name in the org select menu. For most LEAs,
                this is the CD part of the County-District-School (CDS) code. For independently reporting charters, it's the S.
            extract_name (str): generally the four letter acronym of the extract. e.g. SENR, SELA, etc.
                For Direct Certification Extract, pass in extract_name='DirectCertification'.
                Spelling matters, capitalization does not. Silently fails if report name is unrecognized/not supported.
            form_data (list of iterables, optional): a list of the (key, value) pairs to send in the POST request body. To know
                which keys and values are expected, set dry_run=True. Technically optional, but will silently fail if
                a required key is missing.
            by_date_range (bool, optional): some extracts can be requested with a date range parameter.
                Set to True to use date range.
            by_as_of_date (bool, optional): used only in CENR to fill out the As of Date form. If by_date_range is True,
                this is ignored.
            dry_run (bool): when False, it downloads the report. When True, it doesn't download the report and instead
                returns a dict with the form fields and their expected inputs.
        Returns:
            bool: True if extract request was successful, False if it was not successful.
            dict: when dry_run=True, it returns a dict of the form fields and their expected inputs for report manipulation
        """
        extract_name = extract_name.upper()
        if not form_data:
            form_data = list()
        with self.session as session:
            self._select_lea(lea_code)
            # Direct URL access for each extract request with a few exceptions for atypical extracts
            # navigate to extract page
            if extract_name == 'SSID':
                #TODO: Use get_homepage_submission_status and implement the ones needing Job IDs
                raise NotImplementedError("Still in search of a better method to fetch Job IDs.")
                #session.get('https://www.calpads.org/Extract/SSIDExtract')
            elif extract_name == 'DIRECTCERTIFICATION':
                session.get('https://www.calpads.org/Extract/DirectCertificationExtract')
            elif extract_name == 'REJECTEDRECORDS':
                raise NotImplementedError("Still in search of a better method to fetch Job IDs.")
                # session.get('https://www.calpads.org/Extract/RejectedRecords')
            elif extract_name == 'CANDIDATELIST':
                raise NotImplementedError("Still in search of a better method to fetch Job IDs.")
                # session.get('https://www.calpads.org/Extract/CandidateList')
            elif extract_name == 'REPLACEMENTSSID':
                raise NotImplementedError("Still in search of a better method to fetch Job IDs.")
                # session.get('https://www.calpads.org/Extract/ReplacementSSID')
            elif extract_name == 'SPEDDISCREPANCYEXTRACT':
                raise NotImplementedError("Still in search of a better method to fetch Job IDs.")
                # session.get('https://www.calpads.org/Extract/SPEDDiscrepancyExtract')
            elif extract_name == 'DSEAEXTRACT':
                session.get('https://www.calpads.org/Extract/DSEAExtract')
            else:
                #TODO: Let's add some more validation layers here. Maybe through a separate extract module like reports or
                #a config file
                session.get('https://www.calpads.org/Extract/ODSExtract?RecordType={}'.format(extract_name))
            root = etree.fromstring(self.visit_history[-1].text, etree.HTMLParser(encoding='utf8'))

            #In the past, for SPED and SSRV extracts, CALPADS showed SELPA and NonSELPA form options.
            #They have either removed or only show by permission levels, so we won't add that extra layer, for now.
            if by_date_range:
                try:
                    if extract_name != 'CENR':
                        chosen_form = root.xpath('//form[contains(@action, "Extract") and contains(@action, "Date")]')[0]
                    else:
                        chosen_form = root.xpath('//form[contains(@action, "Extract") and contains(@action, "DateRange")]')[0]
                except IndexError:
                    self.log.info("There is no By Date Range request option. Falling back to the default form option.")
                    chosen_form = root.xpath('//form[contains(@action, "Extract") and not(contains(@action, "Date"))]')[0]
            elif extract_name == 'CENR' and by_as_of_date:
                chosen_form = root.xpath('//form[contains(@action, "Extract") and contains(@action, "AsofDate")]')[0]
            else:
                chosen_form = root.xpath('//form[contains(@action, "Extract") and not(contains(@action, "Date"))]')[0]

            extracts_form = ExtractsForm(chosen_form)
            if dry_run:
                return extracts_form.get_parsed_form_fields()

            filled_fields = extracts_form.prefilled_fields.copy() #Safe to do shallow copy; list contents are immutable
            filled_fields.extend(form_data + [('ReportingLEA', lea_code)])
            # Text inputs are not able to submit multiple key values, particularly a problem for Date Range
            filled_fields = extracts_form._filter_text_input_fields(filled_fields)
            #self.log.debug('The submitted form data: {}'.format(filled_fields))

            #self.log.debug('Posting extract request to: {}'.format(urljoin(self.host, chosen_form.attrib['action'])))
            session.post(urljoin(self.host, chosen_form.attrib['action']),
                         data=filled_fields)
            success_text = 'Extract request made successfully.  Please check back later for download.'
            request_response = etree.fromstring(self.visit_history[-1].text, parser=etree.HTMLParser(encoding='utf8'))
            try:
                #self.log.debug(request_response.xpath('//p')[0].text)
                success = (success_text == request_response.xpath('//p')[0].text)
            except IndexError:
                #self.log.debug('Was not able to find a paragraph tag')
                success = False

            return success

    def download_extract(self, lea_code, file_name=None, timeout=60, poll=10):
        """
        Download the file and give it the provided file_name.

        Args:
            lea_code (str): string of the seven digit number found next to your LEA name in the org select menu. For most LEAs,
                this is the CD part of the County-District-School (CDS) code. For independently reporting charters, it's the S.
            file_name (str): the name of the file to pass to open(file_name, 'wb'). Assumes any subdirectories
                parent directories referenced in the file name already exist.
            timeout (int, optional): how long to wait for a completed extract request.
                Defaults to 60 seconds.
            poll (float, optional): this is how long to wait between polls to the API to check if the request is
                complete. This parameter is used in time.sleep(). Defaults to 10 seconds to respect the API, and
                enforces a minimum of 1 second.

        Returns:
            bool: True for a successful download of report, else False.
        """
        if poll < 1:
            poll = 1
        if not file_name:
            file_name = 'data'
        #TODO: Check also for type and download date, all that good stuff
        with self.session as session:
            self._select_lea(lea_code)
            time_start = time.time()
            extract_request_id = None
            while (time.time() - time_start) < timeout:
                result = self.get_requested_extracts(lea_code).get('Data')
                # self.log.debug(result)
                #Currently only pulling the first result to check against, assuming it's the latest
                if result[0]['ExtractStatus'] == 'Complete':
                    extract_request_id = result[0]['ExtractRequestID']
                    break
                #Take a breather
                time.sleep(poll)
            if extract_request_id:
                with open(file_name, 'wb') as f:
                    f.write(self._get_extract_bytes(extract_request_id))
                    return True
            else:
                self.log.info("Download request timed out. The download might have taken too long.")
                return False

    def upload_file(self, lea_code, file_path=None, form_data=None, dry_run=False):
        if not dry_run:
            assert file_path and form_data, "File Path and Form Data are required inputs."
        with self.session as session:
            self._select_lea(lea_code)
            session.get("https://www.calpads.org/FileSubmission/FileUpload")
            root = etree.fromstring(self.visit_history[-1].text,
                                    etree.HTMLParser(encoding='utf8'))
            root_form = root.xpath("//div[@id='fileUpload']//form")[0]
            upload_form = FilesUploadForm(root_form)
            if dry_run:
                return upload_form.get_parsed_form_fields()
            prefilled_form = upload_form.prefilled_fields.copy()
            prefilled_form.extend(form_data)
            prefilled_dict = dict(prefilled_form)
            cleaned_filled_form = {k: v for k,v in prefilled_dict.items() if v != '' and v is not None}
            file_input = {'FilesUploaded[0].FileName': open(file_path, 'rb')}
            session.post(urljoin(self.visit_history[-1].url, root_form.attrib['action']),
                         files=file_input,
                         data=cleaned_filled_form)
            response = etree.fromstring(self.visit_history[-1].text,
                                        etree.HTMLParser(encoding='utf8'))
            if response.xpath('//*[contains(@class, "alert alert-success")]'):
                return True
            else:
                return False

    def post_file(self, lea_code, ignore_rejections=False, timeout=180, poll=30):
        if poll < 10:
            poll = 10
        with self.session as session:
            self._select_lea(lea_code)
            start_time = time.time()
            while (time.time()-start_time) < timeout:
                #TODO: Need to check that this references the correct data and not stale data
                #Maybe 'Ready for Review' ensures the date is never stale?
                get_job_status = self.get_homepage_submission_status().get('Data')[-1]
                if get_job_status['SubmissionStatus'] == 'Ready for Review':
                    if get_job_status['Rejected'] == '0':
                        #safe to post
                        session.get(f"https://www.calpads.org/FileSubmission/Detail/{get_job_status['JobID']}")
                        if self._post_file_post_action().xpath('//*[contains(@class, "alert alert-success")]'):
                            return True
                        else:
                            return False
                    elif get_job_status['Rejected'] != '0' and ignore_rejections:
                        #safe-ish to post
                        self.log.info("There were rejections, but ignoring those rejections.")
                        session.get(f"https://www.calpads.org/FileSubmission/Detail/{get_job_status['JobID']}")
                        if self._post_file_post_action().xpath('//*[contains(@class, "alert alert-success")]'):
                            return True
                        else:
                            return False
                    elif get_job_status['Rejected'] != '0' and not ignore_rejections:
                        self.log.info("Unable to post the latest job because some records were rejected")
                        return False
                else:
                    time.sleep(poll)
            self.log.info("Unable to post the latest job, timed out.")
            return False

    def _post_file_post_action(self):
        root = etree.fromstring(self.visit_history[-1].text,
                                etree.HTMLParser(encoding='utf8'))
        form_root = root.xpath('//form[@action="/FileSubmission/Post"]')[0]
        #TODO: Test beyond just SENR file
        inputs = FilesUploadForm(form_root).prefilled_fields + [('command', 'Post All')]
        input_dict = dict(inputs)
        self.session.post(urljoin(self.host, '/FileSubmission/Post'),
                       data=input_dict)
        response = etree.fromstring(self.visit_history[-1].text,
                                    etree.HTMLParser(encoding='utf8'))
        return response
    def _get_extract_bytes(self, extract_request_id):
        """Get the extract bytes by extract_request_id. Returns bytes."""
        self.session.get(urljoin(self.host, f'/Extract/DownloadLink?ExtractRequestID={extract_request_id}'))
        return self.visit_history[-1].content

    def _select_lea(self, lea_code):
        """Specifies the context of the requests to the provided lea_code.
        Args:
            lea_code (str): string of the seven digit number found next to your LEA name in the org select menu. For most LEAs,
            this is the CD part of the County-District-School (CDS) code. For independently reporting charters, it's the S.

        Returns:
            None
        """
        with self.session as session:
            session.get(self.host)
            page_root = etree.fromstring(self.visit_history[-1].text, parser=etree.HTMLParser(encoding='utf8'))
            orgchange_form = page_root.xpath("//form[contains(@action, 'UserOrgChange')]")[0]
            try:
                org_form_val = (orgchange_form
                                .xpath("//select/option[contains(text(), '{}')]".format(lea_code))[0]
                                .attrib.get('value'))
            except IndexError:
                self.log.info("The provided lea_code, {}, does not appear to exist for you."
                              .format(lea_code))
                raise Exception("Unable to switch to the provided LEA Code")

            request_token = orgchange_form.xpath("//input[@name='__RequestVerificationToken']")[0].get('value')

            session.post(urljoin(self.host, orgchange_form.attrib['action']),
                         data={'selectedItem': org_form_val,
                               '__RequestVerificationToken': request_token})

    def _get_report_link(self, report_code, is_snapshot=False):
        """Fetch and return the URL associated with the report_code"""
        with self.session as session:
            if is_snapshot:
                session.get('https://www.calpads.org/Report/Snapshot')
            else:
                session.get('https://www.calpads.org/Report/ODS')
            response = self.visit_history[-1]
            if report_code == '8.1eoy3' and is_snapshot:
                # TODO: Might add another variable and if-condition to re-use for ODS as well as Snapshot
                return 'https://www.calpads.org/Report/Snapshot/8_1_StudentProfileList_EOY3_'
            else:
                root = etree.fromstring(response.text, parser=etree.HTMLParser(encoding='utf8'))
                elements = root.xpath("//*[@class='num-wrap-in']")
                for element in elements:
                    if report_code == element.text.lower():
                        return urljoin(self.host, element.xpath('./../../a')[0].attrib['href'])
                #TODO: Write this exception in an exceptions.py
                #raise ReportNotFound('{} report code cannot be found on the webpage'.format(report_code))

    def _handle_event_hooks(self, r, *args, **kwargs):
        """This hook is executed with every HTPP request, primarily used to handle instances of OAuth Dance."""
        self.log.debug(("Response STATUS CODE: {}\nChecking hooks for: \n{}\n"
                        .format(r.status_code, r.url)
                        )
                       )
        scheme, netloc, path, query, frag = urlsplit(r.url)
        if path == '/Account/Login' and r.status_code == 200:
            self.log.debug("Handling /Account/Login")
            self.session.cookies.update(r.cookies.get_dict()) #Update the cookies for future requests
            init_root = etree.fromstring(r.text, parser=etree.HTMLParser(encoding='utf8'))
            # Filling the login form
            self.credentials['__RequestVerificationToken'] = (init_root
                                                              .xpath("//input[@name='__RequestVerificationToken']")[0]
                                                              .get('value'))

            self.credentials['ReturnUrl'] = (init_root
                                              .xpath("//input[@id='ReturnUrl']")[0]
                                              .get('value'))

            self.credentials['AgreementConfirmed'] = "True"

            # self.log.debug(self.credentials)
            # Was helpful in debugging bad username & password, but that should probably not hang out on the console :)
            self.session.post(r.url,
                              data=self.credentials
                              )

        elif path in ['/connect/authorize/callback', '/connect/authorize'] and r.status_code == 200:
            self.log.debug("Handling /connect/authorize/callback")
            self.session.cookies.update(r.cookies.get_dict()) #Update the cookies for future requests
            login_root = etree.fromstring(r.text, parser=etree.HTMLParser(encoding='utf8'))

            # Interstitial OpenID Page
            openid_form_data = {input_.attrib.get('name'): input_.attrib.get("value") for input_ in login_root.xpath('//input')}
            action_url = login_root.xpath('//form')[0].attrib.get('action')

            #A check for the when to try to join on self.host
            scheme, netloc, path, query, frag = urlsplit(action_url)
            if (not scheme and not netloc):
                self.session.post(urljoin(self.host, action_url),
                                  data=openid_form_data
                                )
            else:
                self.log.debug("Using the action URL from the OpenID interstitial page: {}"
                               .format(action_url))
                self.session.post(action_url,
                                  data=openid_form_data
                                  )
        else:
            self.log.debug("No response hook needed for: {}\n".format(r.url))
            self.visit_history.append(r)
            return r