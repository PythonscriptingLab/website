# Function to fetch data for the dashboard
def query_dashboard_data():
    conn = get_db()
    total_apps = conn.execute('SELECT COUNT(DISTINCT application_name) FROM servers').fetchone()[0]
    total_servers = conn.execute('SELECT COUNT(*) FROM servers').fetchone()[0]
    total_groups = conn.execute('SELECT COUNT(DISTINCT group_name) FROM servers').fetchone()[0]
    prod_servers = conn.execute('SELECT COUNT(*) FROM servers WHERE environment = "prod"').fetchone()[0]
    uat_servers = conn.execute('SELECT COUNT(*) FROM servers WHERE environment = "uat"').fetchone()[0]
    dev_servers = conn.execute('SELECT COUNT(*) FROM servers WHERE environment = "dev"').fetchone()[0]
    certs_expiring_soon = conn.execute('SELECT COUNT(*) FROM servers WHERE cert_expiry_date < DATE("now", "+30 days")').fetchone()[0]
    servers_rhel7 = conn.execute('SELECT COUNT(*) FROM servers WHERE os_version = "RHEL 7"').fetchone()[0]

    # Query for certificate expiry data
    df_expiry = pd.read_sql_query('''SELECT group_name AS Group,
                                      SUM(CASE WHEN cert_expiry_date < DATE("now", "+45 days") THEN 1 ELSE 0 END) AS "< 45 days",
                                      SUM(CASE WHEN cert_expiry_date >= DATE("now", "+45 days") AND cert_expiry_date < DATE("now", "+90 days") THEN 1 ELSE 0 END) AS "45-90 days",
                                      SUM(CASE WHEN cert_expiry_date >= DATE("now", "+90 days") AND cert_expiry_date < DATE("now", "+120 days") THEN 1 ELSE 0 END) AS "90-120 days",
                                      SUM(CASE WHEN cert_expiry_date >= DATE("now", "+120 days") THEN 1 ELSE 0 END) AS "> 120 days"
                                      FROM servers GROUP BY group_name''', conn)

    # Query for OS version distribution data
    df_os = pd.read_sql_query('''SELECT group_name AS Group,
                                  SUM(CASE WHEN os_version = "RHEL 7" THEN 1 ELSE 0 END) AS "RHEL 7",
                                  SUM(CASE WHEN os_version = "RHEL 8" THEN 1 ELSE 0 END) AS "RHEL 8"
                                  FROM servers GROUP BY group_name''', conn)

    return {
        'total_apps': total_apps,
        'total_servers': total_servers,
        'total_groups': total_groups,
        'prod_servers': prod_servers,
        'uat_servers': uat_servers,
        'dev_servers': dev_servers,
        'certs_expiring_soon': certs_expiring_soon,
        'servers_rhel7': servers_rhel7,
        'df_expiry': df_expiry,
        'df_os': df_os
    }

# Function to create the certificate expiry chart
def create_expiry_chart(df_expiry):
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ['#ff0000', '#ffa500', '#90ee90', '#006400']  # Red, Orange, Light Green, Dark Green
    df_expiry.plot(kind='barh', stacked=True, color=colors, ax=ax, edgecolor='none')
    ax.set_xlabel('Number of Certificates')
    ax.set_ylabel('Group')
    ax.legend(title='Expiry Range', bbox_to_anchor=(1.05, 1), loc='upper left')
    fig.tight_layout(pad=1.0)
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf8')

# Function to create the OS distribution pie chart
def create_os_chart(df_os):
    fig, ax = plt.subplots(figsize=(8, 4))
    os_counts = [df_os['RHEL 7'].sum(), df_os['RHEL 8'].sum()]
    colors = ['#1f77b4', '#aec7e8']  # Blue and Light Blue
    ax.pie(os_counts, labels=['RHEL 7', 'RHEL 8'], autopct='%1.1f%%', startangle=90, colors=colors)
    ax.set_title("OS Version Split-Up")
    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf8')
