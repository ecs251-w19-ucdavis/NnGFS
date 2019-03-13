#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>
#include <ngx_string.h>

#include <string.h>
#include <sqlite3.h>

#define DEFAULT_BATCH 4
#define DEFAULT_CHUNKSIZE 1024 * 1024
#define DEFAULT_CSID "default_csid"
#define DEFAULT_ROOTDIR "/tmp/"
#define DB_PATH "/tmp/tosync.db"

#define SUBREQUEST_MASTER 0

#define ARGS_FILENAME "filename="
#define ARGS_CHUNK "chunk="
#define ARGS_BACKUP "backupcsid="

#define my_strncpy(s1, s2, n) strncpy((char *) s1, (const char *) s2, n)

typedef struct {
    ngx_str_t csid;
    size_t chunksize;
    ngx_uint_t max_batch;
    ngx_str_t root_dir;
} ngx_http_gfs_loc_conf_t;

static int
init_tosync(ngx_conf_t *cf) {
    sqlite3 *db;
    char *err_msg = 0;
    
    int rc = sqlite3_open(DB_PATH, &db);
    
    if (rc != SQLITE_OK) {
        ngx_conf_log_error(NGX_LOG_EMERG, cf, 0,
            "Failed to open database: %s",
            sqlite3_errmsg(db));
        sqlite3_close(db);
        return 1;
    }
    
    char *sql = "DROP TABLE IF EXISTS ToSync; \
                 CREATE TABLE IF NOT EXISTS ToSync ( \
                    cs_id INTEGER NOT NULL, \
                    file_path TEXT NOT NULL, \
                    UNIQUE (cs_id, file_path), \
                    CHECK(LENGTH(file_path) > 0), \
                    CHECK(cs_id > 0) \
                );";

    rc = sqlite3_exec(db, sql, 0, 0, &err_msg);
    
    if (rc != SQLITE_OK) {
        ngx_conf_log_error(NGX_LOG_EMERG, cf, 0,
            "Failed to create table: %s",
            sqlite3_errmsg(db));
        sqlite3_free(err_msg);        
        sqlite3_close(db);
        return 1;
    } 
    
    sqlite3_close(db);
    return 0;
}

static int
insert_tosync(char *file_path, char *backup_str,
              size_t backup_str_len, ngx_log_t *log) {
    int csids[2] = {0,0};
    int first = 1;
    for (unsigned int i = 0; i < backup_str_len; i++) {
        if (*(backup_str + i) == ',') {
            first = 0;
        } else {
            if (first) {
                csids[0] = csids[0] * 10 + (*(backup_str + i) - '0');
            } else {
                csids[1] = csids[1] * 10 + (*(backup_str + i) - '0');
            }
        }
    }
    if (csids[0] == 0 || csids[1] == 0) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "parsed csid: %d %d",
                      csids[0], csids[1]);
        return 1;
    }

    sqlite3 *db;
    sqlite3_stmt *stmt;

    int rc = sqlite3_open(DB_PATH, &db);
    if (rc != SQLITE_OK) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to open database: %s",
                      sqlite3_errmsg(db));
        return 1;
    }

    if (sqlite3_prepare(db, "Insert OR Ignore Into ToSync (file_path, cs_id) values (?, ?), (?, ?);",
        -1, &stmt, 0) != SQLITE_OK) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to prepare query: %s",
                      sqlite3_errmsg(db));
        return 1;
    }
    if (sqlite3_bind_text(stmt, 1, file_path, strlen(file_path), SQLITE_STATIC) != SQLITE_OK) {
        
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to bind 1");
        return 1;
    }
    if (sqlite3_bind_int(stmt, 2, csids[0]) != SQLITE_OK) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to bind 2");
        return 1;
    }
    if (sqlite3_bind_text(stmt, 3, file_path, strlen(file_path), SQLITE_STATIC) != SQLITE_OK) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to bind 3");
        return 1;
    }
    if (sqlite3_bind_int(stmt, 4, csids[1]) != SQLITE_OK) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to bind 4");
        return 1;
    }

    if (sqlite3_step(stmt) != SQLITE_DONE) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to step: %s", sqlite3_errmsg(db));
        return 1;
    }

    sqlite3_finalize(stmt);
    sqlite3_close(db);

    return 0;
}

// return 0 on success, 1 on error
static int
parse_args(ngx_str_t args, ngx_str_t *filename,
    unsigned int *chunk, ngx_log_t *log, int read_request) {
    if (ngx_strncmp(args.data, ARGS_FILENAME, ngx_strlen(ARGS_FILENAME))) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to parse %s[1]", args);
        return 1;
    }
    filename->data = args.data + ngx_strlen(ARGS_FILENAME);

    unsigned char *sign = (unsigned char *)ngx_strchr(args.data, '&');
    if (!sign) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to parse %s[2]", args);
        return 1;
    }

    filename->len = sign - filename->data;

    if (ngx_strncmp(sign + 1, ARGS_CHUNK, ngx_strlen(ARGS_CHUNK))) {
        ngx_log_error(NGX_LOG_ERR, log, 0, "Failed to parse %s[3]", args);
        return 1;
    }

    unsigned char *end;
    if (read_request) {
        end = args.data + args.len;
    } else {
        end = (unsigned char *)ngx_strchr(sign + 1 + ngx_strlen(ARGS_CHUNK), '&');
    }

    unsigned int sum = 0;
    for (unsigned char *tmp = sign + 1 + ngx_strlen(ARGS_CHUNK);
            tmp < end; tmp++) {
        sum = sum * 10 + (*tmp - '0');
    }
    *chunk = sum;
    return 0;
}

static size_t
read_file(unsigned char **buf, const char *root, ngx_str_t* filename,
    unsigned int chunk_id, ngx_http_request_t *r)
{
    char chunk_str[10];
    for (int i = 0; i < 10; i++) {
        chunk_str[i] = '\0';
    }
    sprintf(chunk_str, "%d", chunk_id);
    int len = ngx_strlen(root) + filename->len + 1 + ngx_strlen(chunk_str);
    char* res = (char *)ngx_pcalloc(r->pool, len+1);
    strcpy(res, root);
    strncat(res, (const char *)filename->data, filename->len);
    strcat(res, "/");
    strcat(res, chunk_str);
    res[len] = '\0';

    /* declare a file pointer */
    FILE *infile;
    size_t numbytes;

    /* open an existing file for reading */
    infile = fopen(res, "r");

    /* quit if the file does not exist */
    if (infile == NULL) {
        ngx_log_error(NGX_LOG_ERR, r->connection->log, 0,
            "Failed to read %s[1]", res);
        return 0;
    }

    /* Get the number of bytes */
    fseek(infile, 0L, SEEK_END);
    numbytes = ftell(infile);

    /* reset the file position indicator to
    the beginning of the file */
    fseek(infile, 0L, SEEK_SET);

    /* grab sufficient memory for the
    buffer to hold the text */
    unsigned char * tmp_buf = ngx_palloc(r->pool, numbytes);

    /* memory error */
    if (tmp_buf == NULL) {
        ngx_log_error(NGX_LOG_ERR, r->connection->log, 0,
            "Failed to alloc %d[1]", numbytes);
        if (infile) {
            fclose(infile);
        }
        return 0;
    }

    /* copy all the text into the buffer */
    size_t read_len = fread(tmp_buf, numbytes, 1, infile);
    *buf = tmp_buf;
    fclose(infile);
    return read_len * numbytes;
}

// handler
static ngx_int_t
ngx_http_gfs_handler(ngx_http_request_t *r);

// install module and handler
static char* ngx_http_gfs(ngx_conf_t *cf, ngx_command_t *cmd, void *conf);
// malloc 
static void* ngx_http_gfs_create_loc_conf(ngx_conf_t *cf);

static char* ngx_http_gfs_merge_loc_conf(ngx_conf_t *cf,
    void *parent, void *child);

// read client body
static void gfs_read_client_body(ngx_http_request_t *r);

// subrequest callback
static ngx_int_t
gfs_write_subrequest_post_handler(ngx_http_request_t *r,
    void *data, ngx_int_t rc);

// subrequest write callback
static void gfs_write_post_handler(ngx_http_request_t *r);

// module directives
static ngx_command_t  ngx_http_gfs_commands[] = {
    {   ngx_string("gfs"),
        NGX_HTTP_LOC_CONF|NGX_CONF_NOARGS,
        ngx_http_gfs,
        NGX_HTTP_LOC_CONF_OFFSET,
        0,
        NULL },
    {
        ngx_string("csid"),
        NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,
        ngx_conf_set_str_slot,
        NGX_HTTP_LOC_CONF_OFFSET,
        offsetof(ngx_http_gfs_loc_conf_t, csid),
        NULL },
    {   ngx_string("chunksize"),
        NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,
        ngx_conf_set_size_slot,
        NGX_HTTP_LOC_CONF_OFFSET,
        offsetof(ngx_http_gfs_loc_conf_t, chunksize),
        NULL },
    {   ngx_string("max_batch"),
        NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,
        ngx_conf_set_num_slot,
        NGX_HTTP_LOC_CONF_OFFSET,
        offsetof(ngx_http_gfs_loc_conf_t, chunksize),
        NULL },
    {
        ngx_string("root_dir"),
        NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,
        ngx_conf_set_str_slot,
        NGX_HTTP_LOC_CONF_OFFSET,
        offsetof(ngx_http_gfs_loc_conf_t, root_dir),
        NULL },
    ngx_null_command
};

// module context
static ngx_http_module_t  ngx_http_gfs_module_ctx = {
    NULL,                          /* preconfiguration */
    NULL,  /* postconfiguration */

    NULL,                          /* create main configuration */
    NULL,                          /* init main configuration */

    NULL,                          /* create server configuration */
    NULL,                          /* merge server configuration */

    ngx_http_gfs_create_loc_conf,  /* create location configuration */
    ngx_http_gfs_merge_loc_conf /* merge location configuration */
};

// module definition
ngx_module_t  ngx_http_gfs_module = {
    NGX_MODULE_V1,
    &ngx_http_gfs_module_ctx, /* module context */
    ngx_http_gfs_commands,   /* module directives */
    NGX_HTTP_MODULE,               /* module type */
    NULL,                          /* init master */
    NULL,                          /* init module */
    NULL,                          /* init process */
    NULL,                          /* init thread */
    NULL,                          /* exit thread */
    NULL,                          /* exit process */
    NULL,                          /* exit master */
    NGX_MODULE_V1_PADDING
};

static void gfs_read_client_body(ngx_http_request_t *r)
{
    ngx_http_gfs_loc_conf_t  *gfslcf;
    gfslcf = ngx_http_get_module_loc_conf(r, ngx_http_gfs_module);
    char *root = (char *)gfslcf->root_dir.data;
    ngx_int_t rc;
    ngx_chain_t out;

    // parse arguments
    ngx_str_t filename;
    unsigned int chunk_id = 0;
    if (parse_args(r->args, &filename, &chunk_id, r->connection->log, 0)) {
        ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
        return;
    }
    // get file path
    char chunk_str[10];
    for (int i = 0; i < 10; i++) {
        chunk_str[i] = '\0';
    }
    sprintf(chunk_str, "%d", chunk_id);
    int len = ngx_strlen(root) + filename.len + 1 + ngx_strlen(chunk_str);
    // file path
    char* file_path = (char *)ngx_pcalloc(r->pool, len+1);
    strcpy(file_path, root);
    strncat(file_path, (const char*)filename.data, filename.len);
    strcat(file_path, "/");
    strcat(file_path, chunk_str);
    file_path[len] = '\0';
    // dir path
    char* dir_path = (char *)ngx_pcalloc(r->pool, ngx_strlen(root) + filename.len);
    strcpy(dir_path, root);
    strncat(dir_path, (const char*)filename.data, filename.len);
    dir_path[len] = '\0';

    // create dir if not exists
    struct stat st = {0};
    if (stat(dir_path, &st) == -1) {
        mkdir(dir_path, 0775);
    }

    // read client data and write to file
    FILE* fp = fopen(file_path, "w+");
    if (fp == NULL) {
        ngx_log_error(NGX_LOG_ERR, r->connection->log,
                0, "failed to open %s: %s", file_path, strerror(errno));
        ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
        return;
    }

    ngx_chain_t *request_bufs = r->request_body->bufs;
    ngx_uint_t read = 0;
    for (ngx_chain_t *cl = request_bufs; cl; cl = cl->next) {
        if (cl->buf->last == cl->buf->pos) continue;
        read += cl->buf->last - cl->buf->pos;
        if (fwrite(cl->buf->pos, cl->buf->last - cl->buf->pos, 1, fp) != 1) {
            // TODO how often does this happen, how often does retry help
            ngx_log_error(NGX_LOG_ERR, r->connection->log,
                    0, "Failed to read after %d bytes: %s", read, strerror(errno));
            ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
            return;
        }
    }

    if (fclose(fp)) {
        ngx_log_error(NGX_LOG_ERR, r->connection->log,
                0, "Failed to close file");
        ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
        return;
    }

    // get backup str and add to ToSync table
    char *backup_str = ngx_strstr(r->args.data, ARGS_BACKUP);
    if (backup_str) {
        if (insert_tosync(file_path, backup_str + strlen(ARGS_BACKUP),
                    r->args.len - ((u_char *)backup_str - r->args.data) - strlen(ARGS_BACKUP),
                    r->connection->log)) {
            ngx_log_error(NGX_LOG_ERR, r->connection->log, 0,
                    "Cannot insert tosync");
            ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
            return;
        }
    } else {
        ngx_log_error(NGX_LOG_ERR, r->connection->log,
                0, "Cannot find %s in query", ARGS_BACKUP);
        // JUST NO ARGS_BACKUP argument in query.
        // ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
        // return;
    }

    if (SUBREQUEST_MASTER) {
        // create subrequest
        ngx_http_request_t *sr;
        ngx_str_t uri = ngx_string("/gfs_put/");
        // create subrequest args
        size_t new_args_len = r->args.len + 1 + strlen("csid=") + gfslcf->csid.len + 1;
        char *new_args = ngx_pcalloc(r->pool, new_args_len);
        my_strncpy(new_args, r->args.data, r->args.len);
        new_args[r->args.len] = '&';
        my_strncpy(new_args + r->args.len + 1, "csid=", 5);
        my_strncpy(new_args + r->args.len + 1 + 5, gfslcf->csid.data, gfslcf->csid.len);
        ngx_str_t args = {.data = (u_char *)new_args, .len = new_args_len};

        // alloc subrequest assign handler
        ngx_http_post_subrequest_t *psr = ngx_palloc(r->pool,
                            sizeof(ngx_http_post_subrequest_t));
        if(psr == NULL) {
            ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
            return;
        }
        psr->handler = gfs_write_subrequest_post_handler;
        psr->data = NULL;

        // issue subrequest
        rc = ngx_http_subrequest(r, &uri, &args, &sr, psr, NGX_HTTP_SUBREQUEST_IN_MEMORY);
        if (rc != NGX_OK) {
            ngx_log_error(NGX_LOG_ERR, r->connection->log, 0, 
                "Fail issuing subrequest");
            ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
            return;
        }
    }

    ngx_buf_t *b = ngx_create_temp_buf(r->pool, NGX_OFF_T_LEN);
    if (b == NULL) {
        ngx_http_finalize_request(r, NGX_HTTP_INTERNAL_SERVER_ERROR);
        return;
    }

    b->last = ngx_sprintf(b->pos, "%O", read);
    b->last_buf = 1;
    b->last_in_chain = 1;

    r->headers_out.status = NGX_HTTP_OK;
    r->headers_out.content_length_n = b->last - b->pos;

    rc = ngx_http_send_header(r);

    if (rc == NGX_ERROR || rc > NGX_OK || r->header_only) {
        ngx_http_finalize_request(r, rc);
        return;
    }

    out.buf = b;
    out.next = NULL;

    rc = ngx_http_output_filter(r, &out);

    ngx_http_finalize_request(r, rc);
    
}


static ngx_int_t
ngx_http_gfs_handler(ngx_http_request_t *r)
{
    ngx_buf_t *b;
    ngx_chain_t out;
    ngx_int_t rc;

    ngx_http_gfs_loc_conf_t  *gfslcf;
    gfslcf = ngx_http_get_module_loc_conf(r, ngx_http_gfs_module);

    if (r->method == NGX_HTTP_GET) {
        // parse arguments
        ngx_str_t filename;
        unsigned int chunk = 0;
        if (parse_args(r->args, &filename, &chunk, r->connection->log, 1)) {
            return NGX_ERROR;
        }
        // reading a file
        b = ngx_pcalloc(r->pool, sizeof(ngx_buf_t));
        if (b == NULL) {
            ngx_log_error(NGX_LOG_ERR, r->connection->log, 0, 
            "Failed to allocate response buffer.");
            return NGX_HTTP_INTERNAL_SERVER_ERROR;
        }

        unsigned char* read;
        size_t read_len;
        if ((read_len = read_file(&read, (char *)gfslcf->root_dir.data,
                                  &filename, chunk, r)) == 0) {
            return NGX_ERROR;
        }
        if (read_len > gfslcf->chunksize) {
            read_len = gfslcf->chunksize;
        }

        b->pos = read;
        b->last = read + read_len;

        // set header
        r->headers_out.status = NGX_HTTP_OK;
        r->headers_out.content_length_n = read_len;

        b->memory = 1; /* content is in read-only memory */
        /* (i.e., filters should copy it rather than rewrite in place) */

        b->last_buf = 1; /* there will be no more buffers in the request */

        out.buf = b;
        out.next = NULL;

        rc = ngx_http_send_header(r);

        if (rc == NGX_ERROR || rc > NGX_OK || r->header_only) {
            return rc;
        }
        return ngx_http_output_filter(r, &out);
    } else {
        // write a file
        rc = ngx_http_read_client_request_body(r, gfs_read_client_body);
        if (rc >= NGX_HTTP_SPECIAL_RESPONSE) {
            ngx_log_error(NGX_LOG_ERR, r->connection->log, 0, 
            "bojun rc >= NGX_HTTP_SPECIAL_RESPONSE.");
            return rc;
        }

        return NGX_DONE;
    }

}

static ngx_int_t
gfs_write_subrequest_post_handler(ngx_http_request_t *r,
    void *data, ngx_int_t rc)
{
    ngx_http_request_t *pr = r->parent;
    pr->headers_out.status = r->headers_out.status;

    ngx_buf_t* pRecvBuf = &r->upstream->buffer;
    pRecvBuf->pos = pRecvBuf->last;

    pr->write_event_handler = gfs_write_post_handler;
    return NGX_OK;
}

static void gfs_write_post_handler(ngx_http_request_t *r)
{
    //ngx_int_t ret;
    // if(r->headers_out.status != NGX_HTTP_OK){
    //     ngx_http_finalize_request(r, r->headers_out.status);
    //     return;
    // }
    r->headers_out.content_length_n = 1;
    //r->headers_out.status = NGX_HTTP_OK;
    ngx_buf_t* b = ngx_create_temp_buf(r->pool, 1);
    b->last = b->pos + 1;
    b->last_buf = 1;
    ngx_chain_t out;
    out.buf = b;
    out.next = NULL;
    r->connection->buffered |= NGX_HTTP_WRITE_BUFFERED;
    ngx_http_send_header(r);
    ngx_http_output_filter(r, &out);
}


static char*
ngx_http_gfs(ngx_conf_t *cf, ngx_command_t *cmd, void *conf)
{
    ngx_http_core_loc_conf_t  *clcf;

    clcf = ngx_http_conf_get_module_loc_conf(cf, ngx_http_core_module);
    clcf->handler = ngx_http_gfs_handler;

    if (init_tosync(cf)) {
        return NGX_CONF_ERROR;
    }

    return NGX_CONF_OK;
}


static void *
ngx_http_gfs_create_loc_conf(ngx_conf_t *cf)
{
    ngx_http_gfs_loc_conf_t  *conf;

    conf = ngx_pcalloc(cf->pool, sizeof(ngx_http_gfs_loc_conf_t));
    if (conf == NULL) {
        return NGX_CONF_ERROR;
    }
    conf->chunksize = NGX_CONF_UNSET_SIZE;
    conf->max_batch = NGX_CONF_UNSET_UINT;
    // conf->csid = NGX_CONF_UNSET;
    // conf->root_dir = NGX_CONF_UNSET;
    return conf;
}

static char* ngx_http_gfs_merge_loc_conf(ngx_conf_t *cf,
    void *parent, void *child)
{
    ngx_http_gfs_loc_conf_t *prev = parent;
    ngx_http_gfs_loc_conf_t *conf = child;

    ngx_conf_merge_size_value(conf->chunksize, prev->chunksize, DEFAULT_CHUNKSIZE);
    ngx_conf_merge_uint_value(conf->max_batch, prev->max_batch, DEFAULT_BATCH);
    ngx_conf_merge_str_value(conf->csid, prev->csid, DEFAULT_CSID);
    ngx_conf_merge_str_value(conf->root_dir, prev->root_dir, DEFAULT_ROOTDIR);

    if (conf->max_batch < 1) {
        ngx_conf_log_error(NGX_LOG_EMERG, cf, 0, 
            "max_batch must be equal or more than 1");
        return NGX_CONF_ERROR;
    }

    return NGX_CONF_OK;
}