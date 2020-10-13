--
-- PostgreSQL database dump
--

-- Dumped from database version 10.12
-- Dumped by pg_dump version 10.12

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: main_jobevent_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.main_jobevent_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: main_jobevent; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.main_jobevent (
    id bigint DEFAULT nextval('public.main_jobevent_id_seq'::regclass) NOT NULL,
    created timestamp with time zone,
    modified timestamp with time zone NOT NULL,
    event character varying(100) NOT NULL,
    event_data text NOT NULL,
    failed boolean NOT NULL,
    changed boolean NOT NULL,
    host_name character varying(1024) NOT NULL,
    play character varying(1024) NOT NULL,
    role character varying(1024) NOT NULL,
    task character varying(1024) NOT NULL,
    counter integer NOT NULL,
    host_id integer,
    job_id integer NOT NULL,
    uuid character varying(1024) NOT NULL,
    parent_uuid character varying(1024) NOT NULL,
    end_line integer NOT NULL,
    playbook character varying(1024) NOT NULL,
    start_line integer NOT NULL,
    stdout text NOT NULL,
    verbosity integer NOT NULL,
    CONSTRAINT main_jobevent_counter_check CHECK ((counter >= 0)),
    CONSTRAINT main_jobevent_end_line_check CHECK ((end_line >= 0)),
    CONSTRAINT main_jobevent_start_line_check CHECK ((start_line >= 0)),
    CONSTRAINT main_jobevent_verbosity_check CHECK ((verbosity >= 0))
);


--
-- Name: main_jobevent main_jobevent_pkey1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.main_jobevent
    ADD CONSTRAINT main_jobevent_pkey1 PRIMARY KEY (id);


--
-- Name: main_jobevent_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX main_jobevent_created_idx ON public.main_jobevent USING btree (created);


--
-- Name: main_jobevent_host_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX main_jobevent_host_id_idx ON public.main_jobevent USING btree (host_id);


--
-- Name: main_jobevent_job_id_brin_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX main_jobevent_job_id_brin_idx ON public.main_jobevent USING brin (job_id);


--
-- Name: main_jobevent_job_id_end_line_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX main_jobevent_job_id_end_line_idx ON public.main_jobevent USING btree (job_id, end_line);


--
-- Name: main_jobevent_job_id_event_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX main_jobevent_job_id_event_idx ON public.main_jobevent USING btree (job_id, event);


--
-- Name: main_jobevent_job_id_parent_uuid_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX main_jobevent_job_id_parent_uuid_idx ON public.main_jobevent USING btree (job_id, parent_uuid);


--
-- Name: main_jobevent_job_id_start_line_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX main_jobevent_job_id_start_line_idx ON public.main_jobevent USING btree (job_id, start_line);


--
-- Name: main_jobevent_job_id_uuid_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX main_jobevent_job_id_uuid_idx ON public.main_jobevent USING btree (job_id, uuid);


--
-- PostgreSQL database dump complete
--

