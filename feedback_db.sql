drop database if exists feedback;

create database feedback;

\c feedback

create table users (
    username text primary key unique not null,
    password text not null,
    email text not null,
    first_name text not null,
    last_name text not null
);

create table feedback (
    id serial primary key,
    title text not null,
    content text not null,
    username text references users on delete cascade
);